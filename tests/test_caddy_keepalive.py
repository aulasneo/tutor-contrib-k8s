"""Check Caddy keepalive patch rendering and its opt-out values."""

from pathlib import Path
import unittest

import jinja2
import yaml
from tutor import hooks

from tutork8s.plugin import configure_lms_keepalive


class CaddyKeepaliveTests(unittest.TestCase):
    def test_keepalive_patch(self):
        caddyfile = '''(proxy) {
    reverse_proxy {args.0} {
    }
}
import proxy "lms:8000"
import proxy "cms:8000"
'''
        env = jinja2.Environment(
            loader=jinja2.DictLoader({"apps/caddy/Caddyfile": caddyfile}),
            undefined=jinja2.StrictUndefined,
        )
        env.filters["k8s_lms_keepalive"] = configure_lms_keepalive
        template = env.from_string(
            (Path(__file__).resolve().parents[1] / "tutork8s/patches/kustomization-patches").read_text()
        )
        defaults = dict(hooks.Filters.CONFIG_DEFAULTS.iterate())
        self.assertEqual(defaults["K8S_CADDY_LMS_KEEPALIVE"], "10s")
        defaults.update(LMS_HOST="lms.example.com", CMS_HOST="cms.example.com",
                        K8S_LMS_INGRESS_PROXY_BODY_SIZE="", K8S_CMS_INGRESS_PROXY_BODY_SIZE="")
        for value in ("10s", 0, "0", None, "None", ""):
            with self.subTest(value=value):
                config = dict(defaults, K8S_CADDY_LMS_KEEPALIVE=value)
                patches = yaml.safe_load(template.render(config))
                if value == "10s":
                    rendered = patches[0]["patch"]
                    self.assertEqual(rendered.count("keepalive 10s"), 2)
                    self.assertIn('import proxy "lms:8000" {', rendered)
                    self.assertIn('import proxy "cms:8000" {', rendered)
                else:
                    self.assertIsNone(patches)
