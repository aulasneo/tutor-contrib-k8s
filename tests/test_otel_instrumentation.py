"""Regression coverage for per-site OpenTelemetry workload annotations."""

from pathlib import Path
import unittest

import yaml
from tutor import config, env

import tutork8s.plugin  # noqa: F401; registers templates and defaults

PATCHES = Path(__file__).resolve().parents[1] / "tutork8s/patches"


def render_patch(name, **overrides):
    values = dict(LMS_HOST="lms.example.test", CMS_HOST="cms.example.test")
    values.update(overrides)
    config.update_with_base(values)
    config.update_with_defaults(values)
    config.render_full(values)
    renderer = env.Renderer(values)
    return [
        doc
        for doc in yaml.safe_load_all(renderer.render_str((PATCHES / name).read_text()))
        if doc
    ]


class OTelInstrumentationRenderingTests(unittest.TestCase):
    def test_opted_in_workloads_are_kustomize_patches(self):
        patches = render_patch(
            "k8s-override",
            K8S_OTEL_ENABLE=True,
            K8S_OTEL_INSTRUMENTATION_REF="custom-namespace/custom-python",
        )
        annotations = {
            doc["metadata"]["name"]: doc["spec"]["template"]["metadata"]["annotations"]
            for doc in patches
            if doc.get("kind") == "Deployment"
            and doc.get("spec", {})
            .get("template", {})
            .get("metadata", {})
            .get("annotations")
        }
        self.assertEqual(set(annotations), {"lms", "cms", "lms-worker", "cms-worker"})
        self.assertTrue(
            all(
                item["instrumentation.opentelemetry.io/inject-python"]
                == "custom-namespace/custom-python"
                for item in annotations.values()
            )
        )

    def test_globally_disabled_has_no_injection_annotations(self):
        patches = render_patch("k8s-override", K8S_OTEL_ENABLE=False)
        self.assertFalse(
            any(self.injection_annotation(doc) is not None for doc in patches)
        )

    @staticmethod
    def injection_annotation(doc):
        return (
            doc.get("spec", {})
            .get("template", {})
            .get("metadata", {})
            .get("annotations", {})
            .get("instrumentation.opentelemetry.io/inject-python")
        )

    def test_each_workload_can_opt_out(self):
        workloads = {
            "lms": "K8S_OTEL_LMS_ENABLE",
            "cms": "K8S_OTEL_CMS_ENABLE",
            "lms-worker": "K8S_OTEL_LMS_WORKER_ENABLE",
            "cms-worker": "K8S_OTEL_CMS_WORKER_ENABLE",
        }
        for name, flag in workloads.items():
            with self.subTest(workload=name):
                patches = render_patch(
                    "k8s-override", K8S_OTEL_ENABLE=True, **{flag: False}
                )
                annotated = {
                    doc["metadata"]["name"]
                    for doc in patches
                    if doc.get("kind") == "Deployment"
                    and self.injection_annotation(doc) is not None
                }
                self.assertEqual(annotated, set(workloads) - {name})


if __name__ == "__main__":
    unittest.main()
