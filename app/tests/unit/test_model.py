import datetime
import os
import shutil
import unittest

from sqlalchemy import create_engine

from app import crud
from app import model
from common import posts


class TestModel(unittest.TestCase):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path
    ignition_journal_path = "%s/ignition_journal" % unit_path
    engine = None

    @classmethod
    def setUpClass(cls):
        db = "%s/%s.sqlite" % (cls.dbs_path, TestModel.__name__.lower())
        try:
            os.remove(db)
        except OSError:
            pass
        try:
            shutil.rmtree(cls.ignition_journal_path)
        except OSError:
            pass
        assert os.path.isfile(db) is False
        cls.engine = create_engine('sqlite:///%s' % db)
        model.Base.metadata.create_all(cls.engine)
        fetch = crud.FetchDiscovery(cls.engine, cls.ignition_journal_path)
        assert fetch.get_all_interfaces() == []
        assert fetch.get_all() == []
        assert fetch.get_ignition_journal("") == []
        assert fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"]) == []

    # @unittest.skip("")
    def test_00(self):
        i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M01)
        i.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual([
            {
                'name': u'eth0',
                'as_boot': True,
                'netmask': 21,
                'mac': u'52:54:00:e8:32:5b',
                'ipv4': u'172.20.0.65',
                'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a',
                'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
                'cidrv4': u'172.20.0.65/21',
                "gateway": "172.20.0.1"
            }
        ], interfaces)
        journal = fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"])
        fetch.close()
        self.assertEqual(len(journal), len(posts.M01["ignition-journal"]))

    # @unittest.skip("")
    def test_00_1(self):
        i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M01)
        i.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual([
            {
                'name': u'eth0',
                'as_boot': True,
                'netmask': 21,
                'mac': u'52:54:00:e8:32:5b',
                'ipv4': u'172.20.0.65',
                'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a',
                'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
                'cidrv4': u'172.20.0.65/21',
                "gateway": "172.20.0.1"
            }
        ], interfaces)
        journal = fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"])
        fetch.close()
        self.assertEqual(len(journal), len(posts.M01["ignition-journal"]))

    def test_01(self):
        i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M02)
        i.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(interfaces), 2)
        self.assertEqual(len(fetch.get_ignition_journal(posts.M02["boot-info"]["uuid"])), 39)
        self.assertEqual([
            {
                'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a',
                'mac': u'52:54:00:e8:32:5b',
                'name': u'eth0',
                'cidrv4': u'172.20.0.65/21',
                'as_boot': True,
                'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
                'netmask': 21,
                'ipv4': u'172.20.0.65',
                "gateway": "172.20.0.1"
            },
            {
                'machine': u'a21a9123-302d-488d-976c-5d6ded84a32d',
                'mac': u'52:54:00:a5:24:f5',
                'name': u'eth0',
                'cidrv4': u'172.20.0.51/21',
                'as_boot': True,
                'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
                'netmask': 21,
                'ipv4': u'172.20.0.51',
                "gateway": "172.20.0.1"
            }
        ], interfaces)
        fetch.close()

    def test_02(self):
        m1 = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M01)
        m1.commit_and_close()
        i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M02)
        i.commit_and_close()
        i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M02)
        i.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(interfaces), 2)
        self.assertEqual(len(fetch.get_ignition_journal(posts.M02["boot-info"]["uuid"])), 39)
        self.assertEqual([
            {'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a', 'mac': u'52:54:00:e8:32:5b', 'name': u'eth0',
             'cidrv4': u'172.20.0.65/21', 'as_boot': True, 'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             'netmask': 21, 'ipv4': u'172.20.0.65',
             "gateway": "172.20.0.1"},
            {'machine': u'a21a9123-302d-488d-976c-5d6ded84a32d', 'mac': u'52:54:00:a5:24:f5', 'name': u'eth0',
             'cidrv4': u'172.20.0.51/21', 'as_boot': True, 'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             'netmask': 21, 'ipv4': u'172.20.0.51',
             "gateway": "172.20.0.1"}
        ], interfaces)
        fetch.close()

    def test_03(self):
        i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M03)
        i.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(interfaces), 3)
        self.assertEqual(len(fetch.get_ignition_journal(posts.M03["boot-info"]["uuid"])), 39)

    def test_04(self):
        for p in posts.ALL:
            i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, p)
            i.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))

    def test_05(self):
        for p in posts.ALL:
            i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, p)
            i.commit_and_close()

        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))

    def test_06(self):
        i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M16)
        i.commit_and_close()

    def test_07(self):
        with self.assertRaises(KeyError):
            i = crud.InjectDiscovery(self.engine, self.ignition_journal_path, {
                u'boot-info': {},
                u'lldp': {},
                u'interfaces': []
            })
            i.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))
        machines = fetch.get_all()

        self.assertEqual(len(posts.ALL), len(fetch.get_all()))
        line_nb = 0
        for m in machines:
            line_nb += len(fetch.get_ignition_journal(m["boot-info"]["uuid"]))

        self.assertEqual(587, line_nb)

    def test_08(self):
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        all_data = fetch.get_all_interfaces()
        chassis_names = [k["chassis_name"] for k in all_data]
        self.assertEqual(4, chassis_names.count(None))
        self.assertEqual(19, chassis_names.count("rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4"))

    def test_09(self):
        inject = crud.InjectDiscovery(self.engine, self.ignition_journal_path, posts.M01)
        inject.commit_and_close()
        fetch = crud.FetchDiscovery(self.engine, self.ignition_journal_path)
        all_data_new = fetch.get_all()
        self.assertEqual(all_data_new[0]["boot-info"]["uuid"], posts.M01["boot-info"]["uuid"])

    def test_10(self):
        mac = posts.M01["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 0, 'kubernetes-node': 0, 'etcd-member': 1}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        e = fetch.get_schedules()
        self.assertEqual({mac: [u"etcd-member"]}, e)
        self.assertEqual([u"etcd-member"], fetch.get_roles_by_mac_selector(mac))

    def test_11(self):
        mac = posts.M02["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 0, 'kubernetes-node': 0, 'etcd-member': 2}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual([u"etcd-member"], fetch.get_roles_by_mac_selector(mac))

    def test_12(self):
        mac = posts.M03["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 0, 'kubernetes-node': 0, 'etcd-member': 3}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual([u"etcd-member"], fetch.get_roles_by_mac_selector(mac))

    def test_13(self):
        mac = posts.M04["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-control-plane"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 0, 'etcd-member': 3}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual([u"kubernetes-control-plane"], fetch.get_roles_by_mac_selector(mac))

    def test_14(self):
        mac = posts.M04["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 0, 'etcd-member': 4}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual([u"kubernetes-control-plane", "etcd-member"], fetch.get_roles_by_mac_selector(mac))

    def test_15(self):
        mac = posts.M05["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-node"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 1, 'etcd-member': 4}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual(["kubernetes-node"], fetch.get_roles_by_mac_selector(mac))

    def test_16(self):
        mac = posts.M06["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-node"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 2, 'etcd-member': 4}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual(["kubernetes-node"], fetch.get_roles_by_mac_selector(mac))

    def test_17(self):
        mac = posts.M07["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-node"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 3, 'etcd-member': 4}

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, True))

        inject = crud.InjectSchedule(self.engine, s)
        inject.apply_roles()
        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual(["kubernetes-node"], fetch.get_roles_by_mac_selector(mac))

    def test_18(self):
        mac = posts.M08["boot-info"]["mac"]
        s = {
            "roles": ["bad-role"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 3, 'etcd-member': 4}

        inject = crud.InjectSchedule(self.engine, s)
        with self.assertRaises(AttributeError):
            inject.apply_roles()

        self.assertEqual(inject.commit_and_close(), (e, False))

        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual([], fetch.get_roles_by_mac_selector(mac))

    def test_19(self):
        fetch = crud.FetchSchedule(self.engine)
        self.assertEqual(7, len(fetch.get_schedules()))

    def test_20(self):
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": ""
            }
        }
        with self.assertRaises(AttributeError):
            crud.InjectSchedule(self.engine, s)

    def test_21(self):
        f = crud.FetchSchedule(self.engine)
        r = f.get_role("etcd-member")
        self.assertEqual(4, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(unicode, type(i["mac"]))
            self.assertEqual(unicode, type(i["ipv4"]))
            self.assertEqual(unicode, type(i["cidrv4"]))
            self.assertEqual(unicode, type(i["gateway"]))
            self.assertEqual(unicode, type(i["name"]))
            self.assertEqual(int, type(i["netmask"]))
            self.assertEqual(unicode, type(i["role"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_22(self):
        f = crud.FetchSchedule(self.engine)
        r = f.get_role("kubernetes-node")
        self.assertEqual(3, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(unicode, type(i["mac"]))
            self.assertEqual(unicode, type(i["ipv4"]))
            self.assertEqual(unicode, type(i["cidrv4"]))
            self.assertEqual(unicode, type(i["gateway"]))
            self.assertEqual(unicode, type(i["name"]))
            self.assertEqual(int, type(i["netmask"]))
            self.assertEqual(unicode, type(i["role"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_23(self):
        f = crud.FetchSchedule(self.engine)
        r = f.get_role("kubernetes-control-plane")
        self.assertEqual(1, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(unicode, type(i["mac"]))
            self.assertEqual(unicode, type(i["ipv4"]))
            self.assertEqual(unicode, type(i["cidrv4"]))
            self.assertEqual(unicode, type(i["gateway"]))
            self.assertEqual(unicode, type(i["name"]))
            self.assertEqual(int, type(i["netmask"]))
            self.assertEqual(unicode, type(i["role"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))
