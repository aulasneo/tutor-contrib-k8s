"""Regression coverage for Redis authentication in rendered worker scalers."""

import unittest
from pathlib import Path

import jinja2
import yaml
from tutor import hooks

import tutork8s.plugin  # noqa: F401; registers configuration defaults


class RedisAuthenticationTests(unittest.TestCase):
    def test_worker_authentication(self):
        template = jinja2.Environment(undefined=jinja2.StrictUndefined).from_string(
            (
                Path(__file__).resolve().parents[1] / "tutork8s/patches/k8s-deployments"
            ).read_text(encoding="utf-8")
        )
        for lms, cms in [(False, False), (True, False), (False, True), (True, True)]:
            for username, password in [
                ("", ""),
                ("", "secret"),
                ("user", "secret"),
                ("user", ""),
            ]:
                with self.subTest(
                    lms=lms, cms=cms, username=username, password=password
                ):
                    config = dict(hooks.Filters.CONFIG_DEFAULTS.iterate())
                    config.update(
                        K8S_NAMESPACE="test",
                        LMS_HOST="lms.example.com",
                        CMS_HOST="cms.example.com",
                        REDIS_HOST="redis",
                        REDIS_PORT=6379,
                        OPENEDX_CELERY_REDIS_DB=0,
                        REDIS_USERNAME=username,
                        REDIS_PASSWORD=password,
                        K8S_LMS_WORKER_KEDA_ENABLE=lms,
                        K8S_CMS_WORKER_KEDA_ENABLE=cms,
                    )
                    resources = {}
                    for doc in yaml.safe_load_all(template.render(config)):
                        if not doc:
                            continue
                        key = (doc["kind"], doc["metadata"]["name"])
                        self.assertNotIn(
                            key, resources, f"Duplicate rendered resource: {key}"
                        )
                        resources[key] = doc
                    auth_expected = bool((lms or cms) and password)
                    for kind in ["Secret", "TriggerAuthentication"]:
                        self.assertEqual(
                            (kind, "keda-redis-auth") in resources, auth_expected
                        )
                    if auth_expected:
                        expected = {"password": password}
                        if username:
                            expected["username"] = username
                        self.assertEqual(
                            resources["Secret", "keda-redis-auth"]["stringData"],
                            expected,
                        )
                        references = resources[
                            "TriggerAuthentication", "keda-redis-auth"
                        ]["spec"]["secretTargetRef"]
                        self.assertEqual(
                            {
                                ref["parameter"]: (ref["name"], ref["key"])
                                for ref in references
                            },
                            {key: ("keda-redis-auth", key) for key in expected},
                        )
                    for enabled, name in [(lms, "lms-worker"), (cms, "cms-worker")]:
                        self.assertEqual(("ScaledObject", name) in resources, enabled)
                        if enabled:
                            triggers = resources["ScaledObject", name]["spec"][
                                "triggers"
                            ]
                            self.assertTrue(triggers)
                            for trigger in triggers:
                                self.assertEqual(
                                    trigger.get("authenticationRef"),
                                    {"name": "keda-redis-auth"} if password else None,
                                )


if __name__ == "__main__":
    unittest.main()
