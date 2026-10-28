"""Verify the optional LMS/CMS annotations against a real Kustomize merge."""

import copy
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import jinja2
import yaml
from tutor import hooks

import tutork8s.plugin  # noqa: F401; registers configuration defaults


@unittest.skipUnless(
    shutil.which("kubectl")
    and subprocess.run(
        ["kubectl", "kustomize", "--help"], capture_output=True, check=False
    ).returncode
    == 0,
    "requires kubectl kustomize",
)
class IngressBodySizeTests(unittest.TestCase):
    def test_annotation_merge(self):
        template = jinja2.Environment(undefined=jinja2.StrictUndefined).from_string(
            (
                Path(__file__).resolve().parents[1]
                / "tutork8s/patches/kustomization-patches"
            ).read_text()
        )
        for lms_size, cms_size in [
            ("", ""),
            ("250m", ""),
            ("", "250m"),
            ("100m", "250m"),
            ("0", "0"),
        ]:
            with (
                self.subTest(lms_size=lms_size, cms_size=cms_size),
                tempfile.TemporaryDirectory() as root,
            ):
                config = dict(hooks.Filters.CONFIG_DEFAULTS.iterate())
                config.update(
                    LMS_HOST="elearning.avanxa.com",
                    CMS_HOST="studio.elearning.avanxa.com",
                    K8S_LMS_INGRESS_PROXY_BODY_SIZE=lms_size,
                    K8S_CMS_INGRESS_PROXY_BODY_SIZE=cms_size,
                )
                name = "studio-elearning-avanxa-com-to-caddy"
                ingress = {
                    "apiVersion": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "metadata": {
                        "name": name,
                        "namespace": "avanxa-prod",
                        "annotations": {
                            "cert-manager.io/cluster-issuer": "harmony-letsencrypt-global",
                            "nginx.ingress.kubernetes.io/proxy-body-size": "1m",
                        },
                    },
                    "spec": {
                        "ingressClassName": "nginx",
                        "rules": [
                            {
                                "host": config["CMS_HOST"],
                                "http": {
                                    "paths": [
                                        {
                                            "path": "/",
                                            "pathType": "Prefix",
                                            "backend": {
                                                "service": {
                                                    "name": "caddy",
                                                    "port": {"number": 80},
                                                }
                                            },
                                        }
                                    ]
                                },
                            }
                        ],
                        "tls": [
                            {
                                "hosts": [config["CMS_HOST"]],
                                "secretName": "studio-elearning-avanxa-com-tls",
                            }
                        ],
                    },
                }
                lms = copy.deepcopy(ingress)
                lms["metadata"]["name"] = "elearning-avanxa-com-to-caddy"
                lms["spec"]["rules"][0]["host"] = config["LMS_HOST"]
                lms["spec"]["tls"] = [
                    {
                        "hosts": [config["LMS_HOST"]],
                        "secretName": "elearning-avanxa-com-tls",
                    }
                ]
                other = copy.deepcopy(ingress)
                other["metadata"]["name"] = "apps-elearning-avanxa-com-to-caddy"
                originals = [lms, ingress, other]
                Path(root, "ingresses.yml").write_text(yaml.safe_dump_all(originals))
                patches = yaml.safe_load(template.render(config))
                kustomization = {
                    "apiVersion": "kustomize.config.k8s.io/v1beta1",
                    "kind": "Kustomization",
                    "resources": ["ingresses.yml"],
                }
                if patches:
                    kustomization["patches"] = patches
                else:
                    self.assertEqual((lms_size, cms_size), ("", ""))
                Path(root, "kustomization.yml").write_text(
                    yaml.safe_dump(kustomization)
                )
                result = subprocess.run(
                    ["kubectl", "kustomize", root],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                actual = {
                    doc["metadata"]["name"]: doc
                    for doc in yaml.safe_load_all(result.stdout)
                }
                for original, size in zip(originals, [lms_size, cms_size, ""]):
                    expected = copy.deepcopy(original)
                    if size:
                        expected["metadata"]["annotations"][
                            "nginx.ingress.kubernetes.io/proxy-body-size"
                        ] = size
                    self.assertEqual(actual[original["metadata"]["name"]], expected)
