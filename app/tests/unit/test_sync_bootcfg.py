import json
import os
from unittest import TestCase

from app import sync_bootcfg


class TestConfigSyncSchedules(TestCase):
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path
    api_uri = "http://127.0.0.1:5000"

    def test_00(self):
        s = sync_bootcfg.ConfigSyncSchedules(
            api_uri=self.api_uri,
            bootcfg_path=self.test_bootcfg_path,
            ignition_dict={},
            extra_selector_dict=None,
        )
        d = s.get_dns_attr("r13-srv3.dc-1.foo.bar.cr")
        self.assertEqual({
            'dc': 'dc-1',
            'shortname': 'r13-srv3',
            "rack": "13",
            "pos": "3",
            "domain": "dc-1.foo.bar.cr"
        }, d)

    def test_01(self):
        s = sync_bootcfg.ConfigSyncSchedules(
            api_uri=self.api_uri,
            bootcfg_path=self.test_bootcfg_path,
            ignition_dict={},
            extra_selector_dict=None,
        )
        d = s.get_dns_attr("r13srv3.dc-1.foo.bar.cr")
        self.assertEqual({
            'dc': 'dc-1',
            'shortname': 'r13srv3',
            "rack": "",
            "pos": "",
            "domain": "dc-1.foo.bar.cr"
        }, d)

    def test_02(self):
        s = sync_bootcfg.ConfigSyncSchedules(
            api_uri=self.api_uri,
            bootcfg_path=self.test_bootcfg_path,
            ignition_dict={},
            extra_selector_dict=None,
        )
        d = s.get_dns_attr("kubernetes-control-plane-0")
        self.assertEqual({
            'dc': '',
            'domain': '',
            'pos': '',
            'rack': '',
            'shortname': 'kubernetes-control-plane-0'},
            d)

    def test_03(self):
        s = sync_bootcfg.ConfigSyncSchedules(
            api_uri=self.api_uri,
            bootcfg_path=self.test_bootcfg_path,
            ignition_dict={},
            extra_selector_dict=None,
        )
        d = s.cni_ipam("172.20.0.10/19", "172.20.0.1")
        self.assertEqual(json.dumps({
            'gateway': '172.20.0.1',
            'rangeStart': '172.20.10.1',
            'rangeEnd': '172.20.10.254',
            'routes': [{'dst': '0.0.0.0/0'}],
            'subnet': '172.20.0.0/19',
            'type': 'host-local'}, indent=2),
            json.dumps(d, indent=2))

    def test_04(self):
        s = sync_bootcfg.ConfigSyncSchedules(
            api_uri=self.api_uri,
            bootcfg_path=self.test_bootcfg_path,
            ignition_dict={},
            extra_selector_dict=None,
        )

        sync_bootcfg.ConfigSyncSchedules.range_nb_ips = 60
        sync_bootcfg.ConfigSyncSchedules.skip_ips = 1
        sync_bootcfg.ConfigSyncSchedules.sub_ips = 0

        d = s.cni_ipam("10.99.33.1/19", "10.99.64.254")
        self.assertEqual(json.dumps({
            "type": "host-local",
            "subnet": "10.99.32.0/19",
            "rangeStart": "10.99.33.2",
            "rangeEnd": "10.99.33.62",
            "gateway": "10.99.64.254",
            "routes": [{"dst": "0.0.0.0/0"}]
        }, indent=2), json.dumps(d, indent=2))

    def test_04_1(self):
        s = sync_bootcfg.ConfigSyncSchedules(
            api_uri=self.api_uri,
            bootcfg_path=self.test_bootcfg_path,
            ignition_dict={},
            extra_selector_dict=None,
        )

        sync_bootcfg.ConfigSyncSchedules.range_nb_ips = 60
        sync_bootcfg.ConfigSyncSchedules.skip_ips = 1
        sync_bootcfg.ConfigSyncSchedules.sub_ips = 0

        d = s.cni_ipam("10.99.39.129/19", "10.99.64.254")
        self.assertEqual(json.dumps({
            "type": "host-local",
            "subnet": "10.99.32.0/19",
            "rangeStart": "10.99.39.130",
            "rangeEnd": "10.99.39.190",
            "gateway": "10.99.64.254",
            "routes": [{"dst": "0.0.0.0/0"}]
        }, indent=2), json.dumps(d, indent=2))

    def test_05(self):
        with self.assertRaises(IOError):
            sync_bootcfg.ConfigSyncSchedules(
                api_uri=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_dict={"etcd-member": "no-here"},
                extra_selector_dict=None,
            )
