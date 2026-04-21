# Change log

## Version 21.0.0 (2026-04-21)
- feat: add local development automation with a branding-aligned `Makefile` and dev requirements files
- feat: replace the legacy CI setup with branding-aligned GitHub Actions test and publish workflows
- ref: remove the legacy `setup.py` in favor of `pyproject.toml`
- breaking: require Python 3.11 or newer
- chore: ignore generated Tutor `config.yml` and `env/` artifacts from local test runs
- feat: target Open edX Ulmo with Tutor 21.x

## Version 20.0.0 (2026-03-17)
- feat: target Open edX Teak with Tutor 20.x
- fix: prevent invalid HPA manifests when both CPU and memory metrics are disabled
- doc: sync documentation defaults with the current plugin configuration values

## Version 19.1.0 (2026-01-26)
- feat: add PDB templates for core services with per-service enable toggles
- doc: document PDB enable flags and min-available defaults in settings
- doc: sync memory request defaults to current plugin values
- feat: add VPA templates with per-service enable flags, min/max resource bounds, controlled resources, and update mode settings

## Version 19.0.0 (Initial Release)
- feat: initial release of the Tutor K8s plugin
- feat: add Kubernetes patches for deployments, HPAs, and resource tuning
- feat: expose `K8S_*` settings to configure replicas, autoscaling, and resources
