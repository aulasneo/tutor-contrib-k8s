Changelog
#########

Version 19.1.0 (2026-01-26)
**********

- Added PDB templates for core services with per-service enable toggles.
- Documented PDB enable flags and min-available defaults in settings.
- Synced memory request defaults to current plugin values.
- Added VPA templates with per-service enable flags, min/max resource bounds,
  controlled resources, and update mode settings.

19.0.0 (Initial Release)
************************

- Initial release of the Tutor K8s plugin.
- Adds Kubernetes patches for deployments, HPAs, and resource tuning.
- Exposes ``K8S_*`` settings to configure replicas, autoscaling, and resources.
