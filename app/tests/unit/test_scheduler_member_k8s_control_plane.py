import json
import os
import subprocess
import unittest

from app import scheduler
from common import posts


class TestEtcdSchedulerMember(unittest.TestCase):
    __name__ = "TestEtcdScheduler"
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    app_path = "%s" % os.path.split(tests_path)[0]
    project_path = "%s" % os.path.split(app_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.project_path])
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestEtcdSchedulerMember.test_bootcfg_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s\n\r" % f)
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.clean_sandbox()
        scheduler.CommonScheduler.etcd_initial_cluster_set = set()

    def test_00_get_ip(self):
        ret = scheduler.EtcdMemberK8sControlPlaneScheduler.get_machine_tuple(posts.M01)
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
            scheduler.EtcdMemberK8sControlPlaneScheduler.get_machine_tuple(m)

    # @unittest.skip("skip")
    def test_00(self):
        def fake_fetch_discovery(x, y):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.CommonScheduler.fetch_discovery = fake_fetch_discovery
        sch = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertTrue(sch.apply())
        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with open("%s/groups/%semember-%d.json" % (
                    self.test_bootcfg_path, marker, i)) as group:
                etcd_groups.append(json.loads(group.read()))
        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdschedulermember-emember.yaml")

    # @unittest.skip("skip")
    def test_01(self):
        def fake_fetch_discovery(y):
            return [posts.M01]

        marker = "unit-%s-%s-" % (TestEtcdSchedulerMember.__name__.lower(), self.test_01.__name__)
        sch = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch.fetch_discovery = fake_fetch_discovery
        self.assertFalse(sch.apply())

        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with self.assertRaises(IOError):
                with open("%s/groups/%semember-%d.json" % (
                        self.test_bootcfg_path, marker, i)) as group:
                    etcd_groups.append(json.loads(group.read()))
        self.assertEqual(0, len(etcd_groups))

    # @unittest.skip("skip")
    def test_02(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02]

        marker = "unit-%s-%s-" % (TestEtcdSchedulerMember.__name__.lower(), self.test_01.__name__)
        sch = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch.fetch_discovery = fake_fetch_discovery
        self.assertFalse(sch.apply())

        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with self.assertRaises(IOError):
                with open("%s/groups/%semember-%d.json" % (
                        self.test_bootcfg_path, marker, i)) as group:
                    etcd_groups.append(json.loads(group.read()))
        self.assertEqual(0, len(etcd_groups))

    # @unittest.skip("skip")
    def test_03(self):
        def fake_fetch_discovery(x):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        sch = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        sch.fetch_discovery = fake_fetch_discovery
        self.assertTrue(sch.apply())
        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with open("%s/groups/%semember-%d.json" % (
                    self.test_bootcfg_path, marker, i)) as group:
                etcd_groups.append(json.loads(group.read()))
        self.assertEqual(3, len(etcd_groups))

        self.assertEqual(3, len(sch.done_list))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdschedulermember-emember.yaml")
        self.assertTrue(sch.apply())

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
        self.assertTrue(ref == 3)

    # @unittest.skip("skip")
    def test_04(self):
        def fake_fetch_discovery(x, y):
            return [posts.M01, posts.M02]

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.EtcdMemberK8sControlPlaneScheduler.fetch_discovery = fake_fetch_discovery
        sch = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertFalse(sch.apply())

        sch.fetch_discovery = lambda x: [posts.M01, posts.M02, posts.M03]

        self.assertTrue(sch.apply())
        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with open("%s/groups/%semember-%d.json" % (
                    self.test_bootcfg_path, marker, i)) as group:
                etcd_groups.append(json.loads(group.read()))
        self.assertEqual(3, len(etcd_groups))

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdschedulermember-emember.yaml")
        self.assertTrue(sch.apply())

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
        self.assertTrue(ref == 3)

    # @unittest.skip("skip")
    def test_05(self):
        def fake_fetch_discovery(x, y):
            return None

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.EtcdMemberK8sControlPlaneScheduler.fetch_discovery = fake_fetch_discovery
        sch = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertFalse(sch.apply())

    # @unittest.skip("skip")
    def test_07(self):
        def fake_fetch_discovery(x, y):
            return [posts.M01, posts.M02, posts.M03]

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.EtcdMemberK8sControlPlaneScheduler.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertTrue(sch_cp.apply())

        sch_no = scheduler.K8sNodeScheduler(
            dep_instance=sch_cp,
            ignition_node="%semember" % marker,
        )
        sch_no.fetch_discovery = lambda x: [posts.M01, posts.M02, posts.M03, posts.M04]
        self.assertEqual(1, sch_no.apply())
        self.assertEqual(4, len(sch_no.wide_done_list))
        self.assertEqual(1, len(sch_no.done_list))
        self.assertEqual(3, len(sch_cp.done_list))
        sch_no.fetch_discovery = lambda x: [posts.M01, posts.M02, posts.M03, posts.M04, posts.M05]
        self.assertEqual(2, sch_no.apply())
        self.assertTrue(sch_cp.apply())
        self.assertEqual(3, len(sch_cp.etcd_initial_cluster.split(",")))
        self.assertEqual(3, len(sch_no.etcd_initial_cluster.split(",")))

    # @unittest.skip("skip")
    def test_08(self):
        def fake_fetch_discovery(x, y):
            return [posts.M01, posts.M02, posts.M03, posts.M04, posts.M05]

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.EtcdMemberK8sControlPlaneScheduler.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertTrue(sch_cp.apply())

        sch_no = scheduler.K8sNodeScheduler(
            dep_instance=sch_cp,
            ignition_node="%semember" % marker,
        )
        sch_no.fetch_discovery = lambda x: [posts.M01, posts.M02, posts.M03, posts.M04]
        self.assertEqual(1, sch_no.apply())
        self.assertEqual(4, len(sch_no.wide_done_list))
        self.assertEqual(1, len(sch_no.done_list))
        self.assertEqual(3, len(sch_cp.done_list))
        sch_no.fetch_discovery = lambda x: [posts.M01, posts.M02, posts.M03, posts.M04, posts.M05]
        self.assertEqual(2, sch_no.apply())
        self.assertTrue(sch_cp.apply())
        self.assertEqual(3, len(sch_cp.etcd_initial_cluster.split(",")))
        self.assertEqual(3, len(sch_no.etcd_initial_cluster.split(",")))

    # @unittest.skip("skip")
    def test_09(self):
        def fake_fetch_discovery(x, y):
            return posts.ALL

        marker = "unit-%s-" % (TestEtcdSchedulerMember.__name__.lower())
        scheduler.CommonScheduler.fetch_discovery = fake_fetch_discovery
        sch_cp = scheduler.EtcdMemberK8sControlPlaneScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            bootcfg_prefix=marker)
        self.assertTrue(sch_cp.apply())

        sch_no = scheduler.K8sNodeScheduler(
            dep_instance=sch_cp,
            ignition_node="%semember" % marker,
        )
        self.assertEqual(20, sch_no.apply())
        self.assertTrue(sch_cp.apply())
        expect_initial_cluster = [
            u'static0=http://172.20.0.63:2380',
            u'static1=http://172.20.0.65:2380',
            u'static2=http://172.20.0.51:2380'
        ]
        real_initial_cluster = sch_cp.etcd_initial_cluster.split(",")
        real_initial_cluster.sort()

        self.assertEqual(expect_initial_cluster, real_initial_cluster)
        self.assertEqual(3, len(sch_cp.etcd_initial_cluster.split(",")))
        self.assertEqual(3, len(sch_no.etcd_initial_cluster.split(",")))

    def test_06_ipam(self):
        ipam = scheduler.CommonScheduler.cni_ipam("172.20.0.11/16", "172.20.0.1")
        self.assertEqual(ipam["subnet"], "172.20.0.0/16")
        self.assertEqual(ipam["rangeStart"], "172.20.11.1")
        self.assertEqual(ipam["rangeEnd"], "172.20.11.254")
        self.assertEqual(ipam["routes"][0], {'dst': '0.0.0.0/0'})
        self.assertEqual(ipam["gateway"], "172.20.0.1")
