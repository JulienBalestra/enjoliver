import json
import os
import subprocess
import unittest

from app import scheduler


class TestEtcdScheduler(unittest.TestCase):
    __name__ = "TestEtcdScheduler"
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    app_path = "%s" % os.path.split(tests_path)[0]
    project_path = "%s" % os.path.split(app_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.project_path])

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestEtcdScheduler.test_bootcfg_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s\n\r" % f)
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.clean_sandbox()
        pass

    def test_00(self):
        fake_fetch_interfaces = lambda x, y: {u'interfaces': [
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:ae:b7:a8',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.60',
                 u'CIDRv4': u'172.15.0.60/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:de:a5:52',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.66',
                 u'CIDRv4': u'172.15.0.66/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'', u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:85:26:20',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.61',
                 u'CIDRv4': u'172.15.0.61/16',
                 u'name': u'eth0'}
            ]
        ]}
        marker = "unit-%s-%s-" % (TestEtcdScheduler.__name__.lower(), self.test_00.__name__)
        scheduler.EtcdScheduler.fetch_interfaces = fake_fetch_interfaces
        sch = scheduler.EtcdScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            ignition_proxy="%sproxy" % marker,
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
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.15.0.61:2380,"
                             "static1=http://172.15.0.60:2380,"
                             "static2=http://172.15.0.66:2380")
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdscheduler-test_00-emember.yaml")

    # @unittest.skip("skip")
    def test_01(self):
        fake_fetch_interfaces = lambda x, y: {u'interfaces': [
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:ae:b7:a8',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.60',
                 u'CIDRv4': u'172.15.0.60/16',
                 u'name': u'eth0'}
            ]
        ]}
        marker = "unit-%s-%s-" % (TestEtcdScheduler.__name__.lower(), self.test_01.__name__)
        scheduler.EtcdScheduler.fetch_interfaces = fake_fetch_interfaces
        sch = scheduler.EtcdScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            ignition_proxy="%sproxy" % marker,
            bootcfg_prefix=marker)
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
        fake_fetch_interfaces = lambda x, y: {u'interfaces': [
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:ae:b7:a8',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.60',
                 u'CIDRv4': u'172.15.0.60/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:de:a5:52',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.66',
                 u'CIDRv4': u'172.15.0.66/16',
                 u'name': u'eth0'}
            ]
        ]}
        marker = "unit-%s-%s-" % (TestEtcdScheduler.__name__.lower(), self.test_01.__name__)
        scheduler.EtcdScheduler.fetch_interfaces = fake_fetch_interfaces
        sch = scheduler.EtcdScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            ignition_proxy="%sproxy" % marker,
            bootcfg_prefix=marker)
        self.assertFalse(sch.apply())

        etcd_groups = []
        for i in xrange(sch.etcd_members_nb):
            with self.assertRaises(IOError):
                with open("%s/groups/%semember-%d.json" % (
                        self.test_bootcfg_path, marker, i)) as group:
                    etcd_groups.append(json.loads(group.read()))
        self.assertEqual(0, len(etcd_groups))

    def test_03(self):
        fake_fetch_interfaces = lambda x, y: {u'interfaces': [
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:ae:b7:a8',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.60',
                 u'CIDRv4': u'172.15.0.60/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:de:a5:52',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.66',
                 u'CIDRv4': u'172.15.0.66/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'', u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:85:26:20',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.61',
                 u'CIDRv4': u'172.15.0.61/16',
                 u'name': u'eth0'}
            ]
        ]}
        marker = "unit-%s-%s-" % (TestEtcdScheduler.__name__.lower(), self.test_00.__name__)
        scheduler.EtcdScheduler.fetch_interfaces = fake_fetch_interfaces
        sch = scheduler.EtcdScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            ignition_proxy="%sproxy" % marker,
            bootcfg_prefix=marker)
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
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.15.0.61:2380,"
                             "static1=http://172.15.0.60:2380,"
                             "static2=http://172.15.0.66:2380")
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdscheduler-test_00-emember.yaml")
        self.assertTrue(sch.apply())

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.15.0.61:2380,"
                             "static1=http://172.15.0.60:2380,"
                             "static2=http://172.15.0.66:2380")
        self.assertTrue(ref == 3)

    def test_04(self):
        fake_fetch_interfaces = lambda x, y: {u'interfaces': [
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:ae:b7:a8',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.60',
                 u'CIDRv4': u'172.15.0.60/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:de:a5:52',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.66',
                 u'CIDRv4': u'172.15.0.66/16',
                 u'name': u'eth0'}
            ]

        ]}
        marker = "unit-%s-%s-" % (TestEtcdScheduler.__name__.lower(), self.test_00.__name__)
        scheduler.EtcdScheduler.fetch_interfaces = fake_fetch_interfaces
        sch = scheduler.EtcdScheduler(
            "http://127.0.0.1:5000",
            self.test_bootcfg_path,
            ignition_member="%semember" % marker,
            ignition_proxy="%sproxy" % marker,
            bootcfg_prefix=marker)
        self.assertFalse(sch.apply())
        scheduler.EtcdScheduler.fetch_interfaces = lambda x, y: {u'interfaces': [
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:ae:b7:a8',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.60',
                 u'CIDRv4': u'172.15.0.60/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'',
                 u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:de:a5:52',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.66',
                 u'CIDRv4': u'172.15.0.66/16',
                 u'name': u'eth0'}
            ],
            [
                {u'MAC': u'', u'netmask': 8,
                 u'IPv4': u'127.0.0.1',
                 u'CIDRv4': u'127.0.0.1/8',
                 u'name': u'lo'},

                {u'MAC': u'52:54:00:85:26:20',
                 u'netmask': 16,
                 u'IPv4': u'172.15.0.61',
                 u'CIDRv4': u'172.15.0.61/16',
                 u'name': u'eth0'}
            ]
        ]}
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
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.15.0.61:2380,"
                             "static1=http://172.15.0.60:2380,"
                             "static2=http://172.15.0.66:2380")
        self.assertTrue(ref == 3)

        etcd_profile = "%s/profiles/%semember.json" % (self.test_bootcfg_path, marker)
        with open(etcd_profile) as p:
            p_data = json.loads(p.read())
        self.assertEqual(p_data["ignition_id"],
                         "unit-testetcdscheduler-test_00-emember.yaml")
        self.assertTrue(sch.apply())

        self.assertEqual(3, len(etcd_groups))

        ref = 0
        for g in etcd_groups:
            ref += 1
            self.assertEqual(len(g["metadata"]["etcd_initial_cluster"].split(",")), 3)
            self.assertEqual(g["metadata"]["etcd_initial_cluster"],
                             "static0=http://172.15.0.61:2380,"
                             "static1=http://172.15.0.60:2380,"
                             "static2=http://172.15.0.66:2380")
        self.assertTrue(ref == 3)
