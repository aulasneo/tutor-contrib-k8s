k8s plugin for `Tutor <https://docs.tutor.edly.io>`__
#####################################################

Helper plugin for Kubernetes deployments of Open edX. It extends Tutor's K8s
environment with deployment patches and configuration knobs for autoscaling and
resource sizing of LMS, CMS, their workers, MFEs, and Caddy.

What it does
************

- Adds Kubernetes patch templates that tweak deployments, HPAs, and resource
  requests/limits for Tutor services.
- Exposes ``K8S_*`` configuration settings so you can tune replicas, HPA
  behavior, and resources without editing manifests by hand.
- Includes PodDisruptionBudget resources for core services with configurable
  availability thresholds. Each PDB can be toggled with the
  ``K8S_*_PDB_ENABLE`` settings.


Installation
************

.. code-block:: bash

    pip install git+https://github.com/aulasneo/tutor-contrib-k8s.git

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

Settings and defaults
*********************

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
     - ``300``
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
     - ``300``
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
     - ``100m``
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
     - ``100m``
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
     - ``100m``
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
     - ``100m``
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
   * - ``K8S_CADDY_MAX_UNAVAILABLE_REPLICAS``
     - ``2``
   * - ``K8S_LMS_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_LMS_MAX_UNAVAILABLE_REPLICAS``
     - ``2``
   * - ``K8S_LMS_WORKER_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_LMS_WORKER_MAX_UNAVAILABLE_REPLICAS``
     - ``2``
   * - ``K8S_CMS_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_CMS_MAX_UNAVAILABLE_REPLICAS``
     - ``2``
   * - ``K8S_CMS_WORKER_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_CMS_WORKER_MAX_UNAVAILABLE_REPLICAS``
     - ``2``
   * - ``K8S_MFE_MIN_AVAILABLE_REPLICAS``
     - ``1``
   * - ``K8S_MFE_MAX_UNAVAILABLE_REPLICAS``
     - ``2``

License
*******

This software is licensed under the terms of the AGPLv3.
