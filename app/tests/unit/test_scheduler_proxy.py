import json
import os
import subprocess
import unittest

from app import scheduler
from common import posts


class TestEtcdSchedulerProxy(unittest.TestCase):
    __name__ = "TestEtcdScheduler"
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    app_path = "%s" % os.path.split(tests_path)[0]
    project_path = "%s" % os.path.split(app_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path
    api_uri = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.project_path])
        scheduler.EtcdProxyScheduler.apply_deps_tries = 1
        scheduler.EtcdProxyScheduler.apply_deps_delay = 0
        os.environ["API_URI"] = cls.api_uri

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestEtcdSchedulerProxy.test_bootcfg_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s\n\r" % f)
                    os.remove("%s/%s" % (d, f))

    @staticmethod
    def get_something(things):
        l = []
        d = "%s/%s" % (TestEtcdSchedulerProxy.test_bootcfg_path, things)
        for f in os.listdir(d):
            if ".gitkeep" == f:
                continue
            with open("%s/%s" % (d, f), 'r') as j:
                content = j.read()
            l.append(json.loads(content))
        return l

    @staticmethod
    def get_profiles():
        return TestEtcdSchedulerProxy.get_something("profiles")

    @staticmethod
    def get_groups():
        return TestEtcdSchedulerProxy.get_something("groups")

    def setUp(self):
        self.clean_sandbox()
        scheduler.CommonScheduler.etcd_initial_cluster_set = set()

    def test_00_get_ip(self):
        ret = scheduler.EtcdMemberScheduler.get_machine_tuple(posts.M01)
        self.assertEqual(ret, (u'172.20.0.65', u'52:54:00:e8:32:5b', u'172.20.0.65/21', '172.20.0.1'))

    def test_01_get_ip(self):
        m = {
            "boot-info": {
                "mac": "52:54:00:95:24:0a",
                "uuid": "77fae11f-81ba-4e5f-a2a5-75181887afbc"
            },
            "interfaces": [
                {
                    "cidrv4": "127.0.0.1/8",
                    "ipv4": "127.0.0.1",
                    "mac": "",
                    "name": "lo",
                    "netmask": 8,
                    "gateway": "172.20.0.1"
                },
                {
                    "cidrv4": "172.20.0.57/21",
                    "ipv4": "172.20.0.57",
                    "mac": "52:54:00:95:24:0f",
                    "name": "eth0",
                    "netmask": 21,
                    "gateway": "172.20.0.1"
                }
            ],
            "lldp": {
                "data": {
                    "interfaces": [
                        {
                            "chassis": {
                                "id": "28:f1:0e:12:20:00",
                                "name": "rkt-2253e328-b6b0-42a2-bc38-977a8efb4908"
                            },
                            "port": {
                                "id": "fe:54:00:95:24:0f"
                            }
                        }
                    ]
                },
                "is_file": True
            }
        }
        with self.assertRaises(LookupError):
            scheduler.EtcdMemberScheduler.get_machine_tuple(m)

    # @unittest.skip("skip")
    def test_03(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        self.assertTrue(sch_member.apply())
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker
        )
        self.assertEqual(len(sch_proxy.etcd_initial_cluster.split(",")), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

    # @unittest.skip("skip")
    def test_04(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker,
            apply_first=True
        )
        self.assertEqual(len(sch_proxy.etcd_initial_cluster.split(",")), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

    # @unittest.skip("skip")
    def test_05(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker
        )
        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(sch_proxy.etcd_initial_cluster, "")
        sch_proxy.apply_member()
        self.assertEqual(len(sch_proxy.etcd_initial_cluster.split(",")), 3)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

    # @unittest.skip("skip")
    def test_06(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker,
            apply_first=True
        )
        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_proxy.etcd_initial_cluster.split(",")), 3)
        self.assertEqual(sch_proxy.apply(), 0)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

    # @unittest.skip("skip")
    def test_07(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03, posts.M04]

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker,
            apply_first=True
        )
        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_proxy.etcd_initial_cluster.split(",")), 3)
        self.assertEqual(sch_proxy.apply(), 1)

    # @unittest.skip("skip")
    def test_08(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % TestEtcdSchedulerProxy.__name__.lower()
        sch_member = scheduler.EtcdMemberScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch_member.fetch_discovery = fake_fetch_discovery
        sch_proxy = scheduler.EtcdProxyScheduler(
            etcd_member_instance=sch_member,
            ignition_proxy="%seproxy" % marker,
            apply_first=True
        )
        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(len(sch_proxy.etcd_initial_cluster.split(",")), 3)
        self.assertEqual(sch_proxy.apply(), 0)
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 1)
        groups = self.get_groups()
        self.assertEqual(len(groups), 3)

        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03, posts.M04, posts.M05, posts.M06, posts.M07]

        sch_proxy.fetch_discovery = fake_fetch_discovery
        self.assertEqual(sch_proxy.apply(), 4)
        self.assertEqual(sch_proxy.apply(), 4)
        self.assertEqual(len(sch_member.done_list), 3)
        self.assertEqual(len(sch_member.done_list) + sch_proxy.apply(), len(fake_fetch_discovery(None)))
        profiles = self.get_profiles()
        self.assertEqual(len(profiles), 2)
        groups = self.get_groups()
        self.assertEqual(len(groups), 7)
