# Event-driven autoscaling for Tutor 22

This plugin provides an opt-in KEDA path for Tutor 22 / Open edX Verawood. It
uses demand signals that are closer to the work each deployment performs:

| Workload | Signal | Default target |
| --- | --- | ---: |
| LMS | Caddy in-flight requests for `LMS_HOST` | uWSGI process count, minimum 4 per pod |
| CMS | Caddy in-flight requests for `CMS_HOST` | uWSGI process count, minimum 4 per pod |
| MFE | Caddy in-flight requests for `apps.<LMS_HOST>` | 10 per pod |
| Caddy | Sum of in-flight requests for configured application hosts | 20 per pod |
| LMS worker | Sum of pending Redis list entries in LMS Celery queues | 2 per pod |
| CMS worker | Sum of pending Redis list entries in CMS Celery queues | 2 per pod |

LMS and CMS use the [KEDA Prometheus scaler](https://keda.sh/docs/2.20/scalers/prometheus/).
MFE and Caddy use the [Metrics API scaler][metrics-api] to aggregate gauges
over ready Caddy endpoints. Worker scaling reads Redis directly.

## Prerequisites

- Tutor 22.0.2 or newer in the 22.x series.
- KEDA 2.20 or newer installed and healthy in the cluster. The plugin does not
  install or manage KEDA.
- Before upgrading or enabling LMS/CMS KEDA, configure an existing Prometheus
  server to scrape each Caddy pod once via the metrics Service endpoints at
  `/metrics`, port 9180, with the site's Kubernetes `namespace` label.
  Use a scrape interval well below the averaging window, for example 15–30 s.
  Set `K8S_KEDA_PROMETHEUS_SERVER_ADDRESS` to its query API base URL and
  allow KEDA to reach it. The default DNS name assumes a Service named
  `prometheus` in `monitoring`. The plugin does not install a scraper.
- Network policy, if present, must allow the KEDA operator to reach Caddy pods
  on TCP port 9180 and Redis on its configured port.
- The KEDA operator must retain its standard EndpointSlice read permissions;
  endpoint aggregation depends on them.
- Keep each `K8S_*_REPLICAS` and `K8S_KEDA_FALLBACK_REPLICAS` value at least 1.
  The rendered KEDA minimum and fallback are clamped to one, so this integration
  never scales a workload to zero.

## How web scaling works

When any web KEDA setting is enabled, the plugin:

1. Enables Caddy metrics with bounded `per_host` labels. It deliberately does
   not enable catch-all host observation, which could create unbounded metric
   cardinality.
2. Adds an internal `:9180` Caddy metrics listener and a separate
   `caddy-metrics` ClusterIP Service. Tutor's public `caddy` LoadBalancer Service
   exposes no new port, and no new ingress route is created.
3. Adds a Caddy container startup probe. On each container start it sends a
   local `GET /robots.txt` for every host selected by the enabled web scalers,
   including custom MFE and extra Caddy hosts, with the correct Host header.
   It then verifies that `/metrics` contains each exact host's numeric
   `caddy_http_requests_in_flight{handler="subroute"}` series. Until that
   succeeds, the pod is not ready and is excluded from metrics Service endpoints.
   Kubernetes retries every 10 seconds and restarts the container after 30
   consecutive failures. Probe timeouts allow three seconds per request plus
   time for verification. The probe stops after success; scrapes generate no
   warm-up requests.
4. For LMS and CMS, queries Prometheus for the sum of the per-series
   time averages, filtered by namespace, exact host and `handler="subroute"`.
   The `AverageValue` target expresses concurrency per application replica.
   With `ignoreNullValues: "false"`, missing history counts toward fallback.
   MFE and Caddy read the instantaneous gauges directly from ready endpoints.

`K8S_MFE_KEDA_HOST` defaults to an empty string, which means
`apps.<LMS_HOST>`. Set it explicitly when the MFE host is customized.

The Caddy ScaledObject composes the LMS, CMS, enabled MFE, and
`K8S_CADDY_KEDA_EXTRA_HOSTS` gauges. Extra hosts must correspond to configured
Caddy reverse-proxy hosts; a selector for a nonexistent series makes that
trigger unhealthy and prevents a new Caddy pod from passing its startup probe.

Warm-up requests never use external DNS, an outbound proxy, or redirects.
When Caddy terminates TLS itself, `curl --resolve` keeps the connection local
while supplying the host's SNI; certificate verification is skipped only for
these loopback requests. Caddy must still be able to serve TLS for that host.
In this mode only, the public `caddy` Service publishes unready endpoints so
ACME HTTP/TLS challenges can reach Caddy before certificate issuance completes.
The separate `caddy-metrics` Service still admits only ready pods. This avoids
a certificate/bootstrap deadlock; public traffic may reach a starting pod as
it could before this plugin added the startup probe.
A 404 or upstream 502 on `/robots.txt` is acceptable: it initializes the route
without requiring a healthy application backend. Custom routes should keep
this GET path harmless. A successful HTTP response alone is insufficient;
missing or incompatible metric labels fail verification.

Tutor 22.0.2 ships Caddy 2.11.4. Integration coverage also checks 2.10.2.
Custom Caddy images must provide `/bin/sh`, `curl`, and `awk`, and expose the
per-host `subroute` gauge. Older images such as official 2.9.1 lack `curl`;
upgrade those images before enabling this startup probe. Connection failures,
non-success metrics responses, malformed exposition, and missing series are
not converted to zero. KEDA's existing error handling and fallback remain
unchanged (the Metrics API scaler does not use `ignoreNullValues`).

Run the focused real-Caddy checks with
`RUN_CADDY_TESTS=1 python -m unittest discover -s tests -k fresh` (Docker required).
The normal unit suite checks rendered host coverage and scaler settings.

LMS and CMS use a 60-second scale-up stabilization window and a single
Pods policy allowing one addition per minute. On scale-down the HPA retains
the highest recommendation over 900 seconds and removes at most one pod per
300 seconds. KEDA's cooldown period applies only when scaling down to zero.
For a known event, pre-warm the deployment by raising its minimum replicas.

## How worker scaling works

Celery/Kombu stores a logical priority queue as multiple Redis lists. By
default, the plugin monitors priority steps `0`, `3`, `6`, and `9` for every
configured queue. Priority zero uses the bare queue name; the other lists use
Kombu's `\x06\x16<priority>` suffix. A KEDA scaling modifier sums all physical
lists before applying the queue-length target.

Default logical queues are:

- LMS: `edx.lms.core.default`, `edx.lms.core.high`,
  `edx.lms.core.high_mem`
- CMS: `edx.cms.core.default`, `edx.cms.core.high`, `edx.cms.core.low`

Change the queue-name or priority-step settings if an Open edX customization
changes Celery routing. KEDA connects to `REDIS_HOST:REDIS_PORT` and uses
`OPENEDX_CELERY_REDIS_DB`. If `REDIS_PASSWORD` is configured, the plugin renders a
namespaced Secret and TriggerAuthentication, adding the username only when
`REDIS_USERNAME` is set;
credentials are not placed in ScaledObject metadata. TLS behavior is controlled
by the settings below. See the [KEDA Redis Lists scaler documentation][redis].

Worker scale-down stabilization defaults to 300 seconds. MFE and Caddy default to 120 seconds. The scale-down percentage policy defaults to
100%, alongside a one-pod-per-60-seconds policy. With `selectPolicy: Min`, the
more restrictive policy applies, limiting scale-down to one pod per period.

## Settings

Global settings:

| Setting | Default | Purpose |
| --- | ---: | --- |
| `K8S_KEDA_POLLING_INTERVAL_SECONDS` | `15` | KEDA polling interval |
| `K8S_KEDA_FALLBACK_FAILURE_THRESHOLD` | `3` | Consecutive scaler failures before fallback |
| `K8S_KEDA_FALLBACK_REPLICAS` | `1` | Safe replica count after scaler failures |
| `K8S_KEDA_REDIS_PRIORITY_STEPS` | `[0, 3, 6, 9]` | Kombu physical priority lists |
| `K8S_KEDA_REDIS_TLS_ENABLE` | `false` | Enable TLS for Redis scaler connections |
| `K8S_KEDA_REDIS_UNSAFE_SSL` | `false` | Skip Redis certificate verification; avoid in production |
| `K8S_CADDY_METRICS_PORT` | `9180` | Internal Caddy metrics port |

Settings shared by the LMS and CMS KEDA web scalers:

| Setting | Default |
| --- | --- |
| `K8S_KEDA_PROMETHEUS_SERVER_ADDRESS` | `http://prometheus.monitoring.svc.cluster.local:9090` |
| `K8S_KEDA_INFLIGHT_AVERAGING_WINDOW` | `2m` |
| `K8S_KEDA_WEB_SCALE_UP_STABILIZATION_WINDOW_SECONDS` | `60` |
| `K8S_KEDA_WEB_SCALE_UP_PODS` | `1` |
| `K8S_KEDA_WEB_SCALE_UP_PERIOD_SECONDS` | `60` |
| `K8S_KEDA_WEB_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS` | `900` |
| `K8S_KEDA_WEB_SCALE_DOWN_PODS` | `1` |
| `K8S_KEDA_WEB_SCALE_DOWN_PERIOD_SECONDS` | `300` |

Per-workload settings:

| Setting | Default |
| --- | ---: |
| `K8S_LMS_KEDA_ENABLE` | `false` |
| `K8S_LMS_KEDA_TARGET_INFLIGHT` | Greater of 4 and `OPENEDX_LMS_UWSGI_WORKERS` |
| `K8S_CMS_KEDA_ENABLE` | `false` |
| `K8S_CMS_KEDA_TARGET_INFLIGHT` | Greater of 4 and `OPENEDX_CMS_UWSGI_WORKERS` |
| `K8S_MFE_KEDA_ENABLE` | `false` |
| `K8S_MFE_KEDA_HOST` | empty (`apps.<LMS_HOST>`) |
| `K8S_MFE_KEDA_TARGET_INFLIGHT` | `10` |
| `K8S_CADDY_KEDA_ENABLE` | `false` |
| `K8S_CADDY_KEDA_TARGET_INFLIGHT` | `20` |
| `K8S_CADDY_KEDA_EXTRA_HOSTS` | `[]` |
| `K8S_LMS_WORKER_KEDA_ENABLE` | `false` |
| `K8S_LMS_WORKER_KEDA_QUEUE_NAMES` | LMS queues listed above |
| `K8S_LMS_WORKER_KEDA_TARGET_QUEUE_LENGTH` | `2` |
| `K8S_CMS_WORKER_KEDA_ENABLE` | `false` |
| `K8S_CMS_WORKER_KEDA_QUEUE_NAMES` | CMS queues listed above |
| `K8S_CMS_WORKER_KEDA_TARGET_QUEUE_LENGTH` | `2` |

KEDA reuses each workload's existing replica bounds. For LMS/CMS, migrate
any custom KEDA stabilization windows or rates from the legacy
`K8S_*_HPA_SCALE_*` keys to the settings above. MFE, Caddy and workers
continue to use their workload-specific HPA behavior settings. Enabling KEDA for one
workload omits only that workload's legacy CPU/memory HPA from newly rendered
manifests. Other workloads keep their existing HPA behavior.

## Migration and rollout

Migrate one workload at a time. For example:

```bash
tutor config save \
  --set K8S_LMS_KEDA_ENABLE=true \
  --set K8S_LMS_REPLICAS=1 \
  --set K8S_LMS_MAX_REPLICAS=6
```

Before applying the rendered environment, confirm KEDA is ready:

```bash
kubectl get pods -n keda
kubectl get crd scaledobjects.keda.sh triggerauthentications.keda.sh
```

Kustomize/apply does not prune resources removed from a rendered file. Keep
the legacy HPA until the ScaledObject is ready and its replacement HPA exists.
KEDA normally rejects a ScaledObject targeting a workload with an existing HPA.
For this handover, temporarily disable the [HPA ownership check][hpa-validation]
on the legacy HPA only. This permits a brief overlap between the two HPAs;
complete the deletion promptly because competing HPAs can disrupt scaling.

Run the following as one block. The subshell stops on errors, so a failed apply
or readiness check does not delete the legacy HPA. On a fresh installation, the
missing legacy HPA is skipped:

```bash
(
  set -e
  namespace='<namespace>'
  legacy_hpa=$(kubectl get hpa lms-hpa -n "$namespace" --ignore-not-found -o name)
  if [ -n "$legacy_hpa" ]; then
    kubectl annotate "$legacy_hpa" -n "$namespace" \
      validations.keda.sh/hpa-ownership=false --overwrite
  fi
  kubectl apply -k "$(tutor config printroot)/env"
  kubectl wait scaledobject/lms -n "$namespace" \
    --for=condition=Ready --timeout=120s
  kubectl get hpa lms-keda-hpa -n "$namespace"
  kubectl delete hpa lms-hpa -n "$namespace" --ignore-not-found
)
```

If the block fails, resolve the error and rerun it promptly. To abandon the
migration while the legacy HPA still exists, use the rollback below and remove
its temporary annotation after the legacy environment has been reapplied:

```bash
kubectl annotate hpa lms-hpa -n <namespace> validations.keda.sh/hpa-ownership-
```

Use the corresponding names for other workloads: `cms-hpa`,
`lms-worker-hpa`, `cms-worker-hpa`, `mfe-hpa`, and `caddy-hpa`, with ScaledObject
names matching the workload and replacement HPAs named `<workload>-keda-hpa`.

## Verification

Rendering is safe and does not launch a Tutor site:

```bash
tutor config save
```

After deployment, inspect KEDA and the generated HPA:

```bash
kubectl get scaledobjects,hpa -n <namespace>
kubectl describe scaledobject lms -n <namespace>
kubectl get hpa lms-keda-hpa -n <namespace> --watch
```

For LMS/CMS, run the rendered `spec.triggers[0].metadata.query` in the configured
Prometheus server. Confirm a single numeric sample, and check that the underlying
selector returns one series per scraped Caddy pod. Confirm the HPA shows a
current metric and target and that the ScaledObject's Fallback condition is false.

Test the internal Caddy endpoint from a temporary pod permitted by network
policy and confirm the expected host series exists:

```bash
kubectl run -n <namespace> metrics-check --rm -i --restart=Never \
  --image=curlimages/curl -- \
  curl -fsS http://caddy-metrics.<namespace>.svc.cluster.local:9180/metrics
```

For workers, enqueue representative tasks and confirm every routed task lands
on one of the configured physical queue names. KEDA events and operator logs
will expose Redis authentication, TLS, queue, or metric-selector errors.

## Rollback

Disable KEDA for the workload, render again, delete its ScaledObject and
KEDA-generated HPA, then apply the environment so the legacy HPA is restored:

```bash
tutor config save --set K8S_LMS_KEDA_ENABLE=false
kubectl delete scaledobject lms -n <namespace> --ignore-not-found
kubectl delete hpa lms-keda-hpa -n <namespace> --ignore-not-found
kubectl apply -k "$(tutor config printroot)/env"
```

Apply does not prune shared KEDA resources either. After disabling **all web
KEDA workloads** (LMS, CMS, MFE, and Caddy), remove the metrics Service:

```bash
kubectl delete service caddy-metrics -n <namespace> --ignore-not-found
```

After disabling **both worker KEDA workloads** (LMS worker and CMS worker),
remove the shared Redis authentication objects, including the Secret containing
Redis credentials:

```bash
kubectl delete triggerauthentication keda-redis-auth -n <namespace> --ignore-not-found
kubectl delete secret keda-redis-auth -n <namespace> --ignore-not-found
```

Keep these shared resources while any corresponding KEDA workload still needs
them. For a full rollback, disable all six KEDA settings, delete each workload's
ScaledObject and KEDA HPA, apply the rendered environment, then run both shared
resource cleanup blocks above.

Deleting a ScaledObject does not restore an earlier replica count because
`restoreToOriginalReplicaCount` is disabled. The Deployment remains at its
current count until the restored HPA reconciles it.

[metrics-api]: https://keda.sh/docs/2.20/scalers/metrics-api/
[redis]: https://keda.sh/docs/2.20/scalers/redis-lists/
[caddy-metrics]: https://caddyserver.com/docs/metrics
[hpa-validation]: https://keda.sh/docs/2.20/operate/admission-webhooks/
