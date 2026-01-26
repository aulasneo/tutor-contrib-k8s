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
- Adds VerticalPodAutoscaler templates for core services with configurable
  update mode, min/max allowed resources, and controlled resources.


Installation
************

From Github:

.. code-block:: bash

    pip install git+https://github.com/aulasneo/tutor-contrib-k8s.git

From PyPI:

.. code-block:: bash

    pip install tutor-contrib-k8s

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
     - ``False``
   * - ``K8S_CMS_VPA_MIN_ALLOWED_CPU``
     - ``20m``
   * - ``K8S_CMS_VPA_MAX_ALLOWED_CPU``
     - ``100m``
   * - ``K8S_CMS_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_CMS_VPA_MAX_ALLOWED_MEMORY``
     - ``2Gi``
   * - ``K8S_CMS_WORKER_VPA_ENABLE``
     - ``False``
   * - ``K8S_CMS_WORKER_VPA_MIN_ALLOWED_CPU``
     - ``20m``
   * - ``K8S_CMS_WORKER_VPA_MAX_ALLOWED_CPU``
     - ``100m``
   * - ``K8S_CMS_WORKER_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_CMS_WORKER_VPA_MAX_ALLOWED_MEMORY``
     - ``2Gi``
   * - ``K8S_LMS_VPA_ENABLE``
     - ``False``
   * - ``K8S_LMS_VPA_MIN_ALLOWED_CPU``
     - ``20m``
   * - ``K8S_LMS_VPA_MAX_ALLOWED_CPU``
     - ``100m``
   * - ``K8S_LMS_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_LMS_VPA_MAX_ALLOWED_MEMORY``
     - ``2Gi``
   * - ``K8S_LMS_WORKER_VPA_ENABLE``
     - ``False``
   * - ``K8S_LMS_WORKER_VPA_MIN_ALLOWED_CPU``
     - ``20m``
   * - ``K8S_LMS_WORKER_VPA_MAX_ALLOWED_CPU``
     - ``100m``
   * - ``K8S_LMS_WORKER_VPA_MIN_ALLOWED_MEMORY``
     - ``1.5Gi``
   * - ``K8S_LMS_WORKER_VPA_MAX_ALLOWED_MEMORY``
     - ``2Gi``
   * - ``K8S_MFE_VPA_ENABLE``
     - ``False``
   * - ``K8S_MFE_VPA_MIN_ALLOWED_CPU``
     - ``10m``
   * - ``K8S_MFE_VPA_MAX_ALLOWED_CPU``
     - ``100m``
   * - ``K8S_MFE_VPA_MIN_ALLOWED_MEMORY``
     - ``30Mi``
   * - ``K8S_MFE_VPA_MAX_ALLOWED_MEMORY``
     - ``100Mi``
   * - ``K8S_CADDY_VPA_ENABLE``
     - ``False``
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
