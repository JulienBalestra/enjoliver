#! /usr/bin/env python3
import os
import unittest

import sys

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(PROJECT_PATH, "app")
PYTHON = os.path.join(PROJECT_PATH, "env/bin/python3")
sys.path.append(APP_PATH)

for p in os.listdir(os.path.join(PROJECT_PATH, "env/lib/")):
    PYTHON_LIB = os.path.join(PROJECT_PATH, "env/lib/%s/site-packages" % p)
    sys.path.append(PYTHON_LIB)

from app import (
    configs,
)


class TestValidateMatchboxAssets(unittest.TestCase):
    cwd = os.path.dirname(os.path.abspath(__file__))
    matchbox = os.getenv("CHECK_MATCHBOX_PATH", "%s/matchbox" % cwd)
    assets = "%s/assets" % matchbox

    def test_discoveryC(self):
        rule = "%s/%s/serve" % (self.assets, self.test_discoveryC.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("discoveryC", list_dir)

    def test_enjoliver_agent(self):
        rule = "%s/%s/serve" % (self.assets, self.test_enjoliver_agent.__name__.replace("test_", "").replace("_", "-"))
        list_dir = os.listdir(rule)
        self.assertIn("enjoliver-agent", list_dir)

    def test_coreos(self):
        rule = "%s/%s/serve" % (self.assets, self.test_coreos.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("coreos_production_image.bin.bz2", list_dir)
        self.assertIn("coreos_production_image.bin.bz2.sig", list_dir)
        self.assertIn("coreos_production_image_verity.txt", list_dir)
        self.assertIn("coreos_production_pxe.vmlinuz", list_dir)
        self.assertIn("coreos_production_pxe.vmlinuz.sig", list_dir)
        self.assertIn("coreos_production_pxe_image.cpio.gz", list_dir)
        self.assertIn("coreos_production_pxe_image.cpio.gz.sig", list_dir)
        self.assertIn("version.txt", list_dir)


@unittest.skipIf(os.getenv("SKIP_ACSERVER"), "skip acserver storage")
class TestValidateAcserverStorage(unittest.TestCase):
    cwd = os.path.dirname(os.path.abspath(__file__))
    acserver_d = os.path.join(cwd, "runtime/acserver.d/enjoliver.local")
    ec = configs.EnjoliverConfig(importer=__file__)

    @staticmethod
    def format_image_url(image_url: str):
        image_url = image_url.replace("enjoliver.local/", "")
        image_url = image_url.replace(":", "-")
        return "%s-linux-amd64.aci" % image_url

    def test_cni(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "cni"))
        self.assertEqual(1, len(list_dir))

    def test_etcd(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "etcd"))
        self.assertEqual(1, len(list_dir))

    def test_fleet(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "fleet"))
        self.assertEqual(1, len(list_dir))

    def test_hyperkube(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "hyperkube"))
        self.assertIn(self.format_image_url(self.ec.hyperkube_image_url), list_dir)
        self.assertEqual(1, len(list_dir))

    def test_lldp(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "lldp"))
        self.assertIn(self.format_image_url(self.ec.lldp_image_url), list_dir)
        self.assertEqual(1, len(list_dir))

    def test_iproute2(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "iproute2"))
        self.assertEqual(1, len(list_dir))

    def test_rkt(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "rkt"))
        self.assertEqual(1, len(list_dir))

    def test_rktlet(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "rktlet"))
        self.assertEqual(1, len(list_dir))

    def test_vault(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "vault"))
        self.assertEqual(1, len(list_dir))

    def test_ceph_tools(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "ceph-tools"))
        self.assertIn(self.format_image_url(self.ec.cephtools_image_url), list_dir)
        self.assertEqual(1, len(list_dir))

    def test_dnsmasq(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "dnsmasq"))
        self.assertEqual(1, len(list_dir))

    def test_tiller(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "tiller"))
        self.assertEqual(1, len(list_dir))

    def test_heapster(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "heapster"))
        self.assertEqual(1, len(list_dir))

    def test_node_exporter(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "node-exporter"))
        self.assertEqual(1, len(list_dir))

    def test_kube_state_metrics(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "kube-state-metrics"))
        self.assertEqual(1, len(list_dir))

    def test_prometheus(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "prometheus"))
        self.assertEqual(1, len(list_dir))

    def test_haproxy(self):
        list_dir = os.listdir(os.path.join(self.acserver_d, "haproxy"))
        self.assertEqual(1, len(list_dir))


class TestValidateRuntime(unittest.TestCase):
    cwd = os.path.dirname(os.path.abspath(__file__))
    runtime_d = os.path.join(cwd, "runtime")

    def test_rkt(self):
        self.assertTrue(os.path.isfile(os.path.join(self.runtime_d, "rkt", "rkt")))
        self.assertTrue(os.path.isfile(os.path.join(self.runtime_d, "stage1.d", "coreos.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.runtime_d, "paths.d", "paths.json")))

    def test_helm(self):
        self.assertTrue(os.path.isfile(os.path.join(self.runtime_d, "helm", "helm")))

    def test_acserver(self):
        self.assertTrue(os.path.isfile(os.path.join(self.runtime_d, "acserver", "acserver")))

    def test_matchbox(self):
        self.assertTrue(os.path.isfile(os.path.join(self.runtime_d, "matchbox", "matchbox")))


if __name__ == '__main__':
    unittest.main()
