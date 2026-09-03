# Event-driven autoscaling for Tutor 22

This plugin provides an opt-in KEDA path for Tutor 22 / Open edX Verawood. It
uses demand signals that are closer to the work each deployment performs:

| Workload | Signal | Default target |
| --- | --- | ---: |
| LMS | Caddy in-flight requests for `LMS_HOST` | 1 per pod |
| CMS | Caddy in-flight requests for `CMS_HOST` | 1 per pod |
| MFE | Caddy in-flight requests for `apps.<LMS_HOST>` | 10 per pod |
| Caddy | Sum of in-flight requests for configured application hosts | 20 per pod |
| LMS worker | Sum of pending Redis list entries in LMS Celery queues | 2 per pod |
| CMS worker | Sum of pending Redis list entries in CMS Celery queues | 2 per pod |

There is no Prometheus server or Prometheus Adapter in this design. Caddy emits
Prometheus exposition text, but KEDA's Metrics API scaler reads it directly.
KEDA 2.20 can discover every ready endpoint behind a Kubernetes Service and sum
their values, so Caddy can have multiple replicas without returning a random
replica's gauge. See the [KEDA Metrics API scaler documentation][metrics-api]
and [Caddy metrics documentation][caddy-metrics].

## Prerequisites

- Tutor 22.0.2 or newer in the 22.x series.
- KEDA 2.20 or newer installed and healthy in the cluster. The plugin does not
  install or manage KEDA.
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
   is not modified, and no ingress route or public load balancer port is created.
3. Creates one Metrics API trigger per host. The trigger selects
   `caddy_http_requests_in_flight` with exact `host` and
   `handler="reverse_proxy"` labels, then sums the gauge over all ready Caddy
   endpoints.

`K8S_MFE_KEDA_HOST` defaults to an empty string, which means
`apps.<LMS_HOST>`. Set it explicitly when the MFE host is customized.

The Caddy ScaledObject composes the LMS, CMS, enabled MFE, and
`K8S_CADDY_KEDA_EXTRA_HOSTS` gauges. Extra hosts must correspond to configured
Caddy reverse-proxy hosts; a selector for a nonexistent series makes that
trigger unhealthy.

The in-flight gauge is instantaneous. It reacts well to sustained concurrency,
but a 15-second poll can miss a very short spike. For known events, pre-warm the
deployment by temporarily raising its minimum replicas or use a separate KEDA
cron ScaledObject outside this plugin.

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
`OPENEDX_CELERY_REDIS_DB`. If both `REDIS_USERNAME` and `REDIS_PASSWORD` are
configured, the plugin renders a namespaced Secret and TriggerAuthentication;
credentials are not placed in ScaledObject metadata. TLS behavior is controlled
by the settings below. See the [KEDA Redis Lists scaler documentation][redis].

Worker scale-down stabilization defaults to 600 seconds to avoid removing
capacity during gaps between task bursts. Web workloads retain the existing
300-second default.

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

Per-workload settings:

| Setting | Default |
| --- | ---: |
| `K8S_LMS_KEDA_ENABLE` | `false` |
| `K8S_LMS_KEDA_TARGET_INFLIGHT` | `1` |
| `K8S_CMS_KEDA_ENABLE` | `false` |
| `K8S_CMS_KEDA_TARGET_INFLIGHT` | `1` |
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

KEDA reuses each workload's existing `K8S_*_REPLICAS`,
`K8S_*_MAX_REPLICAS`, and `K8S_*_HPA_SCALE_*` settings. Enabling KEDA for one
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

Kustomize/apply does not prune resources removed from a rendered file. Delete
the old plugin-managed HPA for each migrated workload immediately before
applying its ScaledObject, otherwise two HPAs will write the same Deployment's
replica count:

```bash
kubectl delete hpa lms-hpa -n <namespace>
kubectl apply -k "$(tutor config printroot)/env"
```

Use the corresponding names for other workloads: `cms-hpa`,
`lms-worker-hpa`, `cms-worker-hpa`, `mfe-hpa`, and `caddy-hpa`.

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
kubectl delete scaledobject lms -n <namespace>
kubectl delete hpa lms-keda-hpa -n <namespace> --ignore-not-found
kubectl apply -k "$(tutor config printroot)/env"
```

Deleting a ScaledObject does not restore an earlier replica count because
`restoreToOriginalReplicaCount` is disabled. The Deployment remains at its
current count until the restored HPA reconciles it.

[metrics-api]: https://keda.sh/docs/2.20/scalers/metrics-api/
[redis]: https://keda.sh/docs/2.20/scalers/redis-lists/
[caddy-metrics]: https://caddyserver.com/docs/metrics
