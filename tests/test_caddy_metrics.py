"""Render coverage and opt-in real-Caddy startup regression tests.

Run integration coverage with RUN_CADDY_TESTS=1 python -m unittest discover -s tests.
Docker pulls the official Caddy images; no application backends are required.
"""

import itertools
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import unittest

import yaml
from tutor import config, env

import tutork8s.plugin  # noqa: F401; registers templates and defaults

PATCHES = Path(__file__).resolve().parents[1] / "tutork8s/patches"


def renderer(**overrides):
    values = dict(LMS_HOST="lms.example.test", CMS_HOST="cms.example.test")
    values.update(overrides)
    config.update_with_base(values)
    config.update_with_defaults(values)
    config.render_full(values)
    return env.Renderer(values)


def resources(render, patch):
    return {
        (doc["kind"], doc["metadata"]["name"]): doc
        for doc in yaml.safe_load_all(render.render_str((PATCHES / patch).read_text()))
        if doc
    }


def probe(render):
    deployment = resources(render, "k8s-override")["Deployment", "caddy"]
    return deployment["spec"]["template"]["spec"]["containers"][0].get("startupProbe")


class CaddyRenderingTests(unittest.TestCase):
    def test_probe_hosts_equal_scaler_hosts(self):
        for flags in itertools.product([False, True], repeat=4):
            for tls, proxy in [(False, True), (True, False), (True, True)]:
                with self.subTest(flags=flags, tls=tls, proxy=proxy):
                    render = renderer(
                        **dict(
                            zip(
                                [
                                    "K8S_LMS_KEDA_ENABLE",
                                    "K8S_CMS_KEDA_ENABLE",
                                    "K8S_MFE_KEDA_ENABLE",
                                    "K8S_CADDY_KEDA_ENABLE",
                                ],
                                flags,
                            )
                        ),
                        ENABLE_HTTPS=tls,
                        ENABLE_WEB_PROXY=proxy,
                        K8S_MFE_KEDA_HOST="learning.example.test",
                        K8S_CADDY_KEDA_EXTRA_HOSTS=[
                            "extra.example.test",
                            "lms.example.test",
                        ],
                    )
                    overrides = resources(render, "k8s-override")
                    self.assertEqual(
                        ("Service", "caddy") in overrides,
                        tls and proxy and any(flags),
                    )
                    startup = probe(render)
                    self.assertEqual(startup is not None, any(flags))
                    if not startup:
                        continue
                    command = startup["exec"]["command"]
                    subprocess.run(["sh", "-n", "-c", command[-1]], check=True)
                    warmed = set(re.findall(r"host='([^']+)'", command[-1]))
                    selected = set()
                    for (kind, _), obj in resources(render, "k8s-deployments").items():
                        if kind != "ScaledObject":
                            continue
                        self.assertIn("fallback", obj["spec"])
                        for trigger in obj["spec"]["triggers"]:
                            metadata = trigger["metadata"]
                            self.assertEqual(metadata["format"], "prometheus")
                            self.assertEqual(metadata["aggregationType"], "sum")
                            self.assertEqual(
                                metadata["aggregateFromKubeServiceEndpoints"], "true"
                            )
                            self.assertNotIn("ignoreNullValues", metadata)
                            selected.add(
                                re.search(r'host="([^"]+)"', metadata["valueLocation"])[
                                    1
                                ]
                            )
                    self.assertEqual(warmed, selected)
                    self.assertEqual(
                        "--resolve" in command[-1].split("host='")[1], tls and proxy
                    )
                    self.assertGreater(startup["timeoutSeconds"], 3 * (len(warmed) + 1))

    def test_warmup_is_only_rendered_inside_probe(self):
        self.assertFalse(env.is_rendered("k8s/partials/caddy-metrics-warmup.sh"))

    def test_default_mfe_host(self):
        command = probe(renderer(K8S_MFE_KEDA_ENABLE=True))["exec"]["command"][-1]
        self.assertIn("host='apps.lms.example.test'", command)


@unittest.skipUnless(
    os.environ.get("RUN_CADDY_TESTS") == "1", "requires Docker; set RUN_CADDY_TESTS=1"
)
class CaddyStartupTests(unittest.TestCase):
    def docker(self, *args, check=True):
        return subprocess.run(
            ["docker", *args], text=True, capture_output=True, check=check
        )

    def scrape(self, container):
        return self.docker(
            "exec", container, "curl", "-fsS", "http://127.0.0.1:9180/metrics"
        )

    def test_fresh_replicas_and_failures(self):
        for version in ["2.10.2", "2.11.4"]:
            for tls, proxy in [(False, True), (True, False), (True, True)]:
                with (
                    self.subTest(version=version, tls=tls, proxy=proxy),
                    tempfile.TemporaryDirectory() as root,
                ):
                    render = renderer(
                        ENABLE_HTTPS=tls,
                        ENABLE_WEB_PROXY=proxy,
                        K8S_LMS_KEDA_ENABLE=True,
                        K8S_CMS_KEDA_ENABLE=True,
                        K8S_MFE_KEDA_ENABLE=True,
                        K8S_CADDY_KEDA_ENABLE=True,
                        K8S_MFE_KEDA_HOST="learning.example.test",
                        K8S_CADDY_KEDA_EXTRA_HOSTS=["extra.example.test"],
                    )
                    caddyfile = render.render_template("apps/caddy/Caddyfile")
                    # Exercise actual Tutor LMS/CMS routes plus MFE/custom routes.
                    for host in ["learning.example.test", "extra.example.test"]:
                        caddyfile += f'\n{host}{{$default_site_port}} {{\n import proxy "unavailable:8000"\n}}\n'
                    if tls and proxy:
                        caddyfile = caddyfile.replace("{\n", "{\n local_certs\n", 1)
                    caddyfile += '\n:9181 {\n respond "not prometheus"\n}\n'
                    path = Path(root) / "Caddyfile"
                    path.write_text(caddyfile)
                    command = probe(render)["exec"]["command"]
                    hosts = set(re.findall(r"host='([^']+)'", command[-1]))
                    containers = []
                    try:
                        for _ in range(2):
                            container = self.docker(
                                "run",
                                "-d",
                                "--mount",
                                f"type=bind,src={path},dst=/etc/caddy/Caddyfile,readonly",
                                "-e",
                                f"default_site_port={'' if tls and proxy else ':80'}",
                                f"caddy:{version}",
                                "sh",
                                "-c",
                                "while [ ! -f /tmp/start-caddy ]; do sleep 0.1; done; "
                                "exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile",
                            ).stdout.strip()
                            containers.append(container)
                            # The same probe fails while the listener is not up yet.
                            self.assertNotEqual(
                                self.docker(
                                    "exec", container, *command, check=False
                                ).returncode,
                                0,
                            )
                            self.docker("exec", container, "touch", "/tmp/start-caddy")
                            for attempt in range(30):
                                result = self.docker(
                                    "exec",
                                    container,
                                    "curl",
                                    "-fsS",
                                    "http://127.0.0.1:9180/metrics",
                                    check=False,
                                )
                                if result.returncode == 0:
                                    break
                                time.sleep(0.2)
                            else:
                                self.fail(self.docker("logs", container).stderr)
                            self.assertNotIn('handler="subroute"', result.stdout)
                        for container in containers:
                            result = self.docker(
                                "exec", container, *command, check=False
                            )
                            self.assertEqual(result.returncode, 0, result.stderr)
                            gauges = self.scrape(container).stdout
                            for host in hosts:
                                matches = [
                                    line
                                    for line in gauges.splitlines()
                                    if line.startswith("caddy_http_requests_in_flight{")
                                    and f'host="{host}"' in line
                                    and 'handler="subroute"' in line
                                ]
                                self.assertEqual(len(matches), 1, matches)
                                self.assertEqual(float(matches[0].split()[-1]), 0)
                            # Endpoint failure remains an error, never an invented zero.
                            broken = command[-1].replace(":9180/metrics", ":1/metrics")
                            self.assertNotEqual(
                                self.docker(
                                    "exec", container, "sh", "-ec", broken, check=False
                                ).returncode,
                                0,
                            )
                            malformed = command[-1].replace(
                                ":9180/metrics", ":9181/metrics"
                            )
                            self.assertNotEqual(
                                self.docker(
                                    "exec",
                                    container,
                                    "sh",
                                    "-ec",
                                    malformed,
                                    check=False,
                                ).returncode,
                                0,
                            )
                            # A wrong host still gets an HTTP response, but cannot pass verification.
                            missing = command[-1].replace(
                                "extra.example.test", "missing.example.test"
                            )
                            self.assertNotEqual(
                                self.docker(
                                    "exec", container, "sh", "-ec", missing, check=False
                                ).returncode,
                                0,
                            )
                    finally:
                        for container in containers:
                            self.docker("rm", "-f", container, check=False)


if __name__ == "__main__":
    unittest.main()
