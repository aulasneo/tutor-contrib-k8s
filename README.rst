k8s plugin for `Tutor <https://docs.tutor.edly.io>`__
#####################################################

Helper plugin for Kubernetes deployments of Open edX. It extends Tutor's K8s
environment with deployment patches and configuration knobs for autoscaling and
resource sizing of LMS, CMS, their workers, MFEs, and Caddy.

This release targets Open edX Verawood with Tutor 22.x.

What it does
************

- Adds Kubernetes patch templates that tweak deployments, HPAs, and resource
  requests/limits for Tutor services.
- Adds opt-in KEDA autoscaling for request-serving workloads using Caddy
  in-flight requests and for Celery workers using Redis queue depth. This path
  does not require Prometheus.
- Exposes ``K8S_*`` configuration settings so you can tune replicas, HPA
  behavior, and resources without editing manifests by hand.
- Includes PodDisruptionBudget resources for core services with configurable
  availability thresholds. Each PDB can be toggled with the
  ``K8S_*_PDB_ENABLE`` settings.
- Adds VerticalPodAutoscaler templates for core services with configurable
  update mode, min/max allowed resources, and controlled resources.
- Adds startup, readiness, and liveness probes to the LMS and CMS deployments.
  The startup probe calls the Open edX ``/heartbeat`` endpoint with the required
  internal ``Host`` header, so a pod does not join its Service until Open edX can
  genuinely serve. Readiness and liveness use TCP checks, so a stall in a shared
  dependency cannot eject or restart every replica at once.


Installation
************

From Github:

.. code-block:: bash

    pip install git+https://github.com/aulasneo/tutor-contrib-k8s.git

From PyPI:

.. code-block:: bash

    pip install tutor-contrib-k8s

Install KEDA in the cluster
===========================

KEDA is a cluster-level prerequisite for the event-driven autoscaling features;
this Tutor plugin does not install it. Install KEDA once per Kubernetes cluster,
not once per Tutor site. The account running Helm must be allowed to create
cluster-wide CRDs, RBAC resources, and an APIService. KEDA 2.20 requires
Kubernetes 1.30 or newer.

First confirm that ``kubectl`` points to the intended cluster, then install the
KEDA 2.20 Helm chart in its dedicated namespace:

.. code-block:: bash

    kubectl config current-context
    helm repo add kedacore https://kedacore.github.io/charts
    helm repo update
    helm upgrade --install keda kedacore/keda \
      --namespace keda \
      --create-namespace \
      --version 2.20.0 \
      --wait

Verify that its deployments are available and that the required CRDs and
external metrics API are registered before enabling any ``K8S_*_KEDA_ENABLE``
setting:

.. code-block:: bash

    kubectl wait --namespace keda \
      --for=condition=Available deployment --all --timeout=180s
    kubectl get pods --namespace keda
    kubectl get crd scaledobjects.keda.sh triggerauthentications.keda.sh
    kubectl get apiservice v1beta1.external.metrics.k8s.io

The plugin requires KEDA 2.20 or newer because it uses Metrics API endpoint
aggregation. To upgrade an existing Helm installation, run the same
``helm upgrade --install`` command with a supported newer chart version. See
the `official KEDA deployment guide
<https://keda.sh/docs/2.20/deploy/>`__ for non-Helm installation methods and
cluster-specific options.

Usage
*****

.. code-block:: bash

    tutor plugins enable k8s

Configuration
*************

All settings are regular Tutor config values prefixed with ``K8S_``. You can
set them via ``tutor config save`` or by editing your Tutor config file.

.. code-block:: bash

    tutor config save \
      --set K8S_LMS_REPLICAS=2 \
      --set K8S_LMS_MAX_REPLICAS=6

After changing settings, re-render or redeploy your Tutor K8s environment as
you normally would so the updated templates are applied.

KEDA autoscaling
================

KEDA autoscaling is disabled by default and requires KEDA 2.20 or newer to be
installed separately in the cluster. Enable it per workload with
``K8S_LMS_KEDA_ENABLE``, ``K8S_CMS_KEDA_ENABLE``,
``K8S_LMS_WORKER_KEDA_ENABLE``, ``K8S_CMS_WORKER_KEDA_ENABLE``,
``K8S_MFE_KEDA_ENABLE``, or ``K8S_CADDY_KEDA_ENABLE``. Enabling KEDA for a
workload suppresses that workload's legacy CPU/memory HPA in newly rendered
manifests.

See `the Verawood autoscaling guide
<https://github.com/aulasneo/tutor-contrib-k8s/blob/main/docs/autoscaling-v22.md>`__
for prerequisites, metric design, all settings,
migration, rollout, verification, and rollback instructions.

Health probes
=============

LMS and CMS health probes are enabled by default with
``K8S_OPENEDX_HEALTH_PROBES_ENABLE``. The startup probe calls ``/heartbeat`` on
port 8000 and allows up to 10 minutes for Open edX to initialize. Because
Kubernetes suspends the readiness and liveness probes until the startup probe
first succeeds, no pod joins its Service until Open edX has genuinely answered a
full health check.

Readiness and liveness then use TCP checks on port 8000 rather than
``/heartbeat``. This is deliberate. ``/heartbeat`` verifies MySQL and the
modulestore, which every pod shares, so a database stall fails the probe on all
replicas simultaneously:

- On **liveness**, Kubernetes would restart the whole deployment, turning a short
  dependency blip into a prolonged outage since each replacement pod must pay
  full Open edX startup time.
- On **readiness**, Kubernetes removes every pod from the Service endpoints. The
  ingress then has nowhere to send traffic and refuses connections, so the site
  is completely down even though every pod is healthy and idle. Not restarting
  the pods is little consolation when no request can reach them.

A probe should answer "can *this* pod serve?", not "is the shared database
healthy?". Correlated dependency checks turn a slowdown into an outage, and they
do it at the worst possible moment — under load, when the database is already
struggling. Genuine dependency failures surface as application errors and in
monitoring, which is where they belong.

If every replica has independent dependencies and you want dependency-aware
readiness, set ``K8S_OPENEDX_READINESS_PROBE_USE_HEARTBEAT`` to ``true`` to
restore the ``/heartbeat`` readiness check. Be aware that timing settings alone
are not a safe substitute: a dump holding table locks, or any stall lasting
minutes, will outlast any reasonable ``timeoutSeconds`` × ``failureThreshold``
budget.

The probe timing settings are:

- ``K8S_OPENEDX_STARTUP_PROBE_PERIOD_SECONDS``
- ``K8S_OPENEDX_STARTUP_PROBE_TIMEOUT_SECONDS``
- ``K8S_OPENEDX_STARTUP_PROBE_FAILURE_THRESHOLD``
- ``K8S_OPENEDX_READINESS_PROBE_PERIOD_SECONDS``
- ``K8S_OPENEDX_READINESS_PROBE_TIMEOUT_SECONDS``
- ``K8S_OPENEDX_READINESS_PROBE_FAILURE_THRESHOLD``
- ``K8S_OPENEDX_READINESS_PROBE_USE_HEARTBEAT`` (default ``false``)
- ``K8S_OPENEDX_LIVENESS_PROBE_PERIOD_SECONDS``
- ``K8S_OPENEDX_LIVENESS_PROBE_TIMEOUT_SECONDS``
- ``K8S_OPENEDX_LIVENESS_PROBE_FAILURE_THRESHOLD``

Settings and defaults
*********************

Resource settings
=================

.. list-table::
   :header-rows: 1

   * - Setting suffix
     - Description
   * - ``CPU_REQUEST``
     - Amount of CPU reserved for the pod.
   * - ``MEMORY_REQUEST``
     - Amount of memory reserved for the pod.
   * - ``CPU_LIMIT``
     - Maximum CPU the pod can use; usage above this is throttled.
   * - ``MEMORY_LIMIT``
     - Maximum memory allowed; exceeding this leads to an OOM kill.
   * - ``REPLICAS``
     - Baseline number of replicas when autoscaling is disabled.
   * - ``MAX_REPLICAS``
     - Upper bound for autoscaling.

HPA settings
============

.. list-table::
   :header-rows: 1

   * - Setting suffix
     - Description
   * - ``HPA_ENABLE``
     - Enables HPA creation for the service.
   * - ``HPA_CPU_ENABLE``
     - Enables CPU utilization metrics in the HPA.
   * - ``HPA_MEMORY_ENABLE``
     - Enables memory utilization metrics in the HPA.
   * - ``HPA_CPU_AVERAGE_UTILIZATION``
     - Target average CPU utilization percentage.
   * - ``HPA_MEMORY_AVERAGE_UTILIZATION``
     - Target average memory utilization percentage.
   * - ``HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS``
     - Window to stabilize scale-up recommendations.
   * - ``HPA_SCALE_UP_PERCENT``
     - Max scale-up change as a percentage per period.
   * - ``HPA_SCALE_UP_PODS``
     - Max scale-up change as a number of pods per period.
   * - ``HPA_SCALE_UP_PERIOD_SECONDS``
     - Period for scale-up policies in seconds.
   * - ``HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS``
     - Window to stabilize scale-down recommendations.
   * - ``HPA_SCALE_DOWN_PERCENT``
     - Max scale-down change as a percentage per period.
   * - ``HPA_SCALE_DOWN_PODS``
     - Max scale-down change as a number of pods per period.
   * - ``HPA_SCALE_DOWN_PERIOD_SECONDS``
     - Period for scale-down policies in seconds.

PDB settings
============

.. list-table::
   :header-rows: 1

   * - Setting suffix
     - Description
   * - ``PDB_ENABLE``
     - Enables PodDisruptionBudget creation for the service.
   * - ``MIN_AVAILABLE_REPLICAS``
     - Minimum number of replicas that must remain available.

VPA settings
============

.. list-table::
   :header-rows: 1

   * - Setting suffix
     - Description
   * - ``VPA_ENABLE``
     - Enables VerticalPodAutoscaler creation for the service.
   * - ``VPA_MIN_ALLOWED_CPU``
     - Minimum CPU the VPA can recommend.
   * - ``VPA_MAX_ALLOWED_CPU``
     - Maximum CPU the VPA can recommend.
   * - ``VPA_MIN_ALLOWED_MEMORY``
     - Minimum memory the VPA can recommend.
   * - ``VPA_MAX_ALLOWED_MEMORY``
     - Maximum memory the VPA can recommend.
   * - ``VPA_CONTROLLED_RESOURCES``
     - Resource types controlled by VPA (``cpu`` and/or ``memory``).
   * - ``VPA_UPDATE_MODE``
     - Update mode for applying recommendations (``Off``, ``Initial``, ``Auto``).

Default settings
================

.. list-table::
   :header-rows: 1

   * - Setting
     - Default
   * - ``K8S_VERSION``
     - Plugin version
   * - ``K8S_LMS_HPA_CPU_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_LMS_HPA_MEMORY_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_LMS_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS``
     - ``0``
   * - ``K8S_LMS_HPA_SCALE_UP_PERCENT``
     - ``100``
   * - ``K8S_LMS_HPA_SCALE_UP_PODS``
     - ``4``
   * - ``K8S_LMS_HPA_SCALE_UP_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_LMS_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS``
     - ``300``
   * - ``K8S_LMS_HPA_SCALE_DOWN_PERCENT``
     - ``10``
   * - ``K8S_LMS_HPA_SCALE_DOWN_PODS``
     - ``1``
   * - ``K8S_LMS_HPA_SCALE_DOWN_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_CMS_HPA_CPU_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_CMS_HPA_MEMORY_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_CMS_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS``
     - ``0``
   * - ``K8S_CMS_HPA_SCALE_UP_PERCENT``
     - ``100``
   * - ``K8S_CMS_HPA_SCALE_UP_PODS``
     - ``4``
   * - ``K8S_CMS_HPA_SCALE_UP_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_CMS_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS``
     - ``300``
   * - ``K8S_CMS_HPA_SCALE_DOWN_PERCENT``
     - ``10``
   * - ``K8S_CMS_HPA_SCALE_DOWN_PODS``
     - ``1``
   * - ``K8S_CMS_HPA_SCALE_DOWN_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_LMS_WORKER_HPA_CPU_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_LMS_WORKER_HPA_MEMORY_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_LMS_WORKER_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS``
     - ``0``
   * - ``K8S_LMS_WORKER_HPA_SCALE_UP_PERCENT``
     - ``100``
   * - ``K8S_LMS_WORKER_HPA_SCALE_UP_PODS``
     - ``4``
   * - ``K8S_LMS_WORKER_HPA_SCALE_UP_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_LMS_WORKER_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS``
     - ``600``
   * - ``K8S_LMS_WORKER_HPA_SCALE_DOWN_PERCENT``
     - ``10``
   * - ``K8S_LMS_WORKER_HPA_SCALE_DOWN_PODS``
     - ``1``
   * - ``K8S_LMS_WORKER_HPA_SCALE_DOWN_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_CMS_WORKER_HPA_CPU_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_CMS_WORKER_HPA_MEMORY_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_CMS_WORKER_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS``
     - ``0``
   * - ``K8S_CMS_WORKER_HPA_SCALE_UP_PERCENT``
     - ``100``
   * - ``K8S_CMS_WORKER_HPA_SCALE_UP_PODS``
     - ``4``
   * - ``K8S_CMS_WORKER_HPA_SCALE_UP_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_CMS_WORKER_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS``
     - ``600``
   * - ``K8S_CMS_WORKER_HPA_SCALE_DOWN_PERCENT``
     - ``10``
   * - ``K8S_CMS_WORKER_HPA_SCALE_DOWN_PODS``
     - ``1``
   * - ``K8S_CMS_WORKER_HPA_SCALE_DOWN_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_MFE_HPA_CPU_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_MFE_HPA_MEMORY_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_MFE_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS``
     - ``0``
   * - ``K8S_MFE_HPA_SCALE_UP_PERCENT``
     - ``100``
   * - ``K8S_MFE_HPA_SCALE_UP_PODS``
     - ``4``
   * - ``K8S_MFE_HPA_SCALE_UP_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_MFE_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS``
     - ``300``
   * - ``K8S_MFE_HPA_SCALE_DOWN_PERCENT``
     - ``10``
   * - ``K8S_MFE_HPA_SCALE_DOWN_PODS``
     - ``1``
   * - ``K8S_MFE_HPA_SCALE_DOWN_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_CADDY_HPA_CPU_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_CADDY_HPA_MEMORY_AVERAGE_UTILIZATION``
     - ``80``
   * - ``K8S_CADDY_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS``
     - ``0``
   * - ``K8S_CADDY_HPA_SCALE_UP_PERCENT``
     - ``100``
   * - ``K8S_CADDY_HPA_SCALE_UP_PODS``
     - ``4``
   * - ``K8S_CADDY_HPA_SCALE_UP_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_CADDY_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS``
     - ``300``
   * - ``K8S_CADDY_HPA_SCALE_DOWN_PERCENT``
     - ``10``
   * - ``K8S_CADDY_HPA_SCALE_DOWN_PODS``
     - ``1``
   * - ``K8S_CADDY_HPA_SCALE_DOWN_PERIOD_SECONDS``
     - ``60``
   * - ``K8S_CMS_CPU_REQUEST``
     - ``20m``
   * - ``K8S_CMS_MEMORY_REQUEST``
     - ``1.5Gi``
   * - ``K8S_CMS_CPU_LIMIT``
     - ``100m``
   * - ``K8S_CMS_MEMORY_LIMIT``
     - ``2Gi``
   * - ``K8S_CMS_REPLICAS``
     - ``1``
   * - ``K8S_CMS_MAX_REPLICAS``
     - ``3``
   * - ``K8S_CMS_WORKER_CPU_REQUEST``
     - ``20m``
   * - ``K8S_CMS_WORKER_MEMORY_REQUEST``
     - ``1.5Gi``
   * - ``K8S_CMS_WORKER_CPU_LIMIT``
     - ``100m``
   * - ``K8S_CMS_WORKER_MEMORY_LIMIT``
     - ``2Gi``
   * - ``K8S_CMS_WORKER_REPLICAS``
     - ``1``
   * - ``K8S_CMS_WORKER_MAX_REPLICAS``
     - ``3``
   * - ``K8S_LMS_CPU_REQUEST``
     - ``20m``
   * - ``K8S_LMS_MEMORY_REQUEST``
     - ``1.5Gi``
   * - ``K8S_LMS_CPU_LIMIT``
     - ``100m``
   * - ``K8S_LMS_MEMORY_LIMIT``
     - ``2Gi``
   * - ``K8S_LMS_REPLICAS``
     - ``1``
   * - ``K8S_LMS_MAX_REPLICAS``
     - ``3``
   * - ``K8S_LMS_WORKER_CPU_REQUEST``
     - ``20m``
   * - ``K8S_LMS_WORKER_MEMORY_REQUEST``
     - ``1.5Gi``
   * - ``K8S_LMS_WORKER_CPU_LIMIT``
     - ``100m``
   * - ``K8S_LMS_WORKER_MEMORY_LIMIT``
     - ``2Gi``
   * - ``K8S_LMS_WORKER_REPLICAS``
     - ``1``
   * - ``K8S_LMS_WORKER_MAX_REPLICAS``
     - ``3``
   * - ``K8S_MFE_CPU_REQUEST``
     - ``10m``
   * - ``K8S_MFE_MEMORY_REQUEST``
     - ``30Mi``
   * - ``K8S_MFE_CPU_LIMIT``
     - ``100m``
   * - ``K8S_MFE_MEMORY_LIMIT``
     - ``100Mi``
   * - ``K8S_MFE_REPLICAS``
     - ``1``
   * - ``K8S_MFE_MAX_REPLICAS``
     - ``3``
   * - ``K8S_CADDY_CPU_REQUEST``
     - ``10m``
   * - ``K8S_CADDY_MEMORY_REQUEST``
     - ``50Mi``
   * - ``K8S_CADDY_CPU_LIMIT``
     - ``100m``
   * - ``K8S_CADDY_MEMORY_LIMIT``
     - ``100Mi``
   * - ``K8S_CADDY_REPLICAS``
     - ``1``
   * - ``K8S_CADDY_MAX_REPLICAS``
     - ``3``
   * - ``K8S_CMS_PDB_ENABLE``
     - ``True``
   * - ``K8S_CMS_WORKER_PDB_ENABLE``
     - ``True``
   * - ``K8S_LMS_PDB_ENABLE``
     - ``True``
   * - ``K8S_LMS_WORKER_PDB_ENABLE``
     - ``True``
   * - ``K8S_MFE_PDB_ENABLE``
     - ``True``
   * - ``K8S_CADDY_PDB_ENABLE``
     - ``True``
   * - ``K8S_CADDY_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_LMS_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_LMS_WORKER_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_CMS_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_CMS_WORKER_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_MFE_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_VPA_CONTROLLED_RESOURCES``
     - ``["cpu"]``
   * - ``K8S_VPA_UPDATE_MODE``
     - ``Off``
   * - ``K8S_CMS_VPA_ENABLE``
     - ``True``
   * - ``K8S_CMS_VPA_MIN_ALLOWED_CPU``
     - ``10m``
   * - ``K8S_CMS_VPA_MAX_ALLOWED_CPU``
     - ``1000m``
   * - ``K8S_CMS_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_CMS_VPA_MAX_ALLOWED_MEMORY``
     - ``4Gi``
   * - ``K8S_CMS_WORKER_VPA_ENABLE``
     - ``True``
   * - ``K8S_CMS_WORKER_VPA_MIN_ALLOWED_CPU``
     - ``10m``
   * - ``K8S_CMS_WORKER_VPA_MAX_ALLOWED_CPU``
     - ``1000m``
   * - ``K8S_CMS_WORKER_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_CMS_WORKER_VPA_MAX_ALLOWED_MEMORY``
     - ``4Gi``
   * - ``K8S_LMS_VPA_ENABLE``
     - ``True``
   * - ``K8S_LMS_VPA_MIN_ALLOWED_CPU``
     - ``10m``
   * - ``K8S_LMS_VPA_MAX_ALLOWED_CPU``
     - ``1000m``
   * - ``K8S_LMS_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_LMS_VPA_MAX_ALLOWED_MEMORY``
     - ``4Gi``
   * - ``K8S_LMS_WORKER_VPA_ENABLE``
     - ``True``
   * - ``K8S_LMS_WORKER_VPA_MIN_ALLOWED_CPU``
     - ``10m``
   * - ``K8S_LMS_WORKER_VPA_MAX_ALLOWED_CPU``
     - ``1000m``
   * - ``K8S_LMS_WORKER_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_LMS_WORKER_VPA_MAX_ALLOWED_MEMORY``
     - ``4Gi``
   * - ``K8S_MFE_VPA_ENABLE``
     - ``True``
   * - ``K8S_MFE_VPA_MIN_ALLOWED_CPU``
     - ``10m``
   * - ``K8S_MFE_VPA_MAX_ALLOWED_CPU``
     - ``100m``
   * - ``K8S_MFE_VPA_MIN_ALLOWED_MEMORY``
     - ``30Mi``
   * - ``K8S_MFE_VPA_MAX_ALLOWED_MEMORY``
     - ``100Mi``
   * - ``K8S_CADDY_VPA_ENABLE``
     - ``True``
   * - ``K8S_CADDY_VPA_MIN_ALLOWED_CPU``
     - ``10m``
   * - ``K8S_CADDY_VPA_MAX_ALLOWED_CPU``
     - ``100m``
   * - ``K8S_CADDY_VPA_MIN_ALLOWED_MEMORY``
     - ``50Mi``
   * - ``K8S_CADDY_VPA_MAX_ALLOWED_MEMORY``
     - ``100Mi``

License
*******

This software is licensed under the terms of the AGPLv3.
