#! /usr/bin/env python
import os
import unittest


class TestValidateBootcfgAssets(unittest.TestCase):
    cwd = os.path.dirname(os.path.abspath(__file__))
    bootcfg = os.getenv("CHECK_BOOTCFG_PATH", "%s/bootcfg" % cwd)
    assets = "%s/assets" % bootcfg

    def test_cni(self):
        rule = "%s/%s/serve" % (self.assets, self.test_cni.__name__.replace("test_", ""))
        self.assertIn("cni.tar.gz", os.listdir(rule))

    def test_coreos(self):
        rule = "%s/%s/serve" % (self.assets, self.test_coreos.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("coreos_production_pxe.vmlinuz", list_dir)
        self.assertIn("coreos_production_pxe_image.cpio.gz", list_dir)

    def test_discoveryC(self):
        rule = "%s/%s/serve" % (self.assets, self.test_discoveryC.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("discoveryC", list_dir)

    def test_hyperkube(self):
        rule = "%s/%s/serve" % (self.assets, self.test_hyperkube.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("hyperkube", list_dir)

    def test_lldp(self):
        rule = "%s/%s/serve" % (self.assets, self.test_lldp.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("static-aci-lldp-0.aci", list_dir)

    def test_rkt(self):
        rule = "%s/%s/serve" % (self.assets, self.test_rkt.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("rkt.tar.gz", list_dir)

    def test_setup_network_environment(self):
        rule = "%s/%s/serve" % (
            self.assets, self.test_setup_network_environment.__name__.replace("test_", "").replace("_", "-"))
        list_dir = os.listdir(rule)
        self.assertIn("setup-network-environment", list_dir)


if __name__ == '__main__':
    unittest.main()
