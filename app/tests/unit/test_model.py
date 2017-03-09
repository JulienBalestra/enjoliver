import datetime
import os
import shutil
import unittest
import time

from app import configs
from app import crud
from app import model
from app import smartdb
from common import posts

ec = configs.EnjoliverConfig()


class TestModel(unittest.TestCase):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path
    ignition_journal_path = "%s/ignition_journal" % unit_path

    # engine = None

    @classmethod
    def setUpClass(cls):
        try:
            shutil.rmtree(cls.ignition_journal_path)
        except OSError:
            pass

        if "sqlite:///" in ec.db_uri:

            db = "%s/%s.sqlite" % (cls.dbs_path, TestModel.__name__.lower())

            if True:
                try:
                    os.remove(db)
                except OSError:
                    pass
                assert os.path.isfile(db) is False
                ec.db_uri = 'sqlite:///%s' % db
            else:
                ec.db_uri = 'sqlite:///:memory:'

        cls.smart = smartdb.SmartClient(ec.db_uri)
        model.BASE.metadata.drop_all(cls.smart.get_engine_connection())
        model.BASE.metadata.create_all(cls.smart.get_engine_connection())
        with cls.smart.connected_session() as session:
            crud.health_check(session, time.time(), "unittest")
        with cls.smart.connected_session() as session:
            fetch = crud.FetchDiscovery(session, cls.ignition_journal_path)
            assert fetch.get_all_interfaces() == []
            assert fetch.get_all() == []
            assert fetch.get_ignition_journal("") == []
            assert fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"]) == []

    # @unittest.skip("")
    def test_00(self):

        with self.smart.connected_session() as session:
            i = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M01)
            i.commit()
        with self.smart.connected_session() as session:
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
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
                    "gateway": "172.20.0.1",
                    'fqdn': None,
                }
            ], interfaces)
            journal = fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"])
            self.assertEqual(len(journal), len(posts.M01["ignition-journal"]))

    # @unittest.skip("")
    def test_00_1(self):
        with self.smart.connected_session() as session:
            i = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M01)
            i.commit()

        with self.smart.connected_session() as session:
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
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
                    "gateway": "172.20.0.1",
                    'fqdn': None,
                }
            ], interfaces)

        with self.smart.connected_session() as session:
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            journal = fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"])
            self.assertEqual(len(journal), len(posts.M01["ignition-journal"]))

    def test_01(self):
        with self.smart.connected_session() as session:
            i = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M02)
            i.commit()
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
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
                    "gateway": "172.20.0.1",
                    'fqdn': None,

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
                    "gateway": "172.20.0.1",
                    'fqdn': None,
                }
            ], interfaces)

    def test_02(self):
        with self.smart.connected_session() as session:
            m1 = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M01)
            m1.commit()
            i = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M02)
            i.commit()
            i = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M02)
            i.commit()
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            interfaces = fetch.get_all_interfaces()
            self.assertEqual(len(interfaces), 2)
            self.assertEqual(len(fetch.get_ignition_journal(posts.M02["boot-info"]["uuid"])), 39)
            self.assertEqual([
                {'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a', 'mac': u'52:54:00:e8:32:5b', 'name': u'eth0',
                 'cidrv4': u'172.20.0.65/21', 'as_boot': True,
                 'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
                 'netmask': 21, 'ipv4': u'172.20.0.65', 'fqdn': None,
                 "gateway": "172.20.0.1"},
                {'machine': u'a21a9123-302d-488d-976c-5d6ded84a32d', 'mac': u'52:54:00:a5:24:f5', 'name': u'eth0',
                 'cidrv4': u'172.20.0.51/21', 'as_boot': True,
                 'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
                 'netmask': 21, 'ipv4': u'172.20.0.51', 'fqdn': None,
                 "gateway": "172.20.0.1"}
            ], interfaces)

    def test_03(self):
        with self.smart.connected_session() as session:
            i = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M03)
            i.commit()
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            interfaces = fetch.get_all_interfaces()
            self.assertEqual(len(interfaces), 3)
            self.assertEqual(len(fetch.get_ignition_journal(posts.M03["boot-info"]["uuid"])), 39)

    def test_04(self):
        with self.smart.connected_session() as session:
            for p in posts.ALL:
                i = crud.InjectDiscovery(session, self.ignition_journal_path, p)
                i.commit()
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            interfaces = fetch.get_all_interfaces()
            self.assertEqual(len(posts.ALL), len(interfaces))

    def test_05(self):
        with self.smart.connected_session() as session:
            for p in posts.ALL:
                i = crud.InjectDiscovery(session, self.ignition_journal_path, p)
                i.commit()

            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            interfaces = fetch.get_all_interfaces()
            self.assertEqual(len(posts.ALL), len(interfaces))

    def test_06(self):
        with self.smart.connected_session() as session:
            i = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M16)
            i.commit()

    def test_07(self):
        with self.smart.connected_session() as session:
            with self.assertRaises(KeyError):
                i = crud.InjectDiscovery(session, self.ignition_journal_path, {
                    u'boot-info': {},
                    u'lldp': {},
                    u'interfaces': []
                })
                i.commit()
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            interfaces = fetch.get_all_interfaces()
            self.assertEqual(len(posts.ALL), len(interfaces))
            machines = fetch.get_all()

            self.assertEqual(len(posts.ALL), len(fetch.get_all()))
            line_nb = 0
            for m in machines:
                line_nb += len(fetch.get_ignition_journal(m["boot-info"]["uuid"]))

            self.assertEqual(587, line_nb)

    def test_08(self):
        with self.smart.connected_session() as session:
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            all_data = fetch.get_all_interfaces()
            chassis_names = [k["chassis_name"] for k in all_data]
            self.assertEqual(4, chassis_names.count(None))
            self.assertEqual(19, chassis_names.count("rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4"))

    def test_09(self):
        with self.smart.connected_session() as session:
            inject = crud.InjectDiscovery(session, self.ignition_journal_path, posts.M01)
            inject.commit()
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            all_data_new = fetch.get_all()
            self.assertEqual(all_data_new[0]["boot-info"]["uuid"], posts.M01["boot-info"]["uuid"])

    def test_091(self):
        p = {
            u'boot-info': {
                u'random-id': u'618e2763-7ff6-4493-babd-54503896bbe0',
                u'mac': u'40:a8:f0:3d:ed:a0',
                u'uuid': u'30343536-3998-5a00-4a34-343630353047'
            },
            u'lldp': {
                u'data': {
                    u'interfaces': None
                }, u'is_file': True
            },
            u'interfaces': [
                {u'name': u'lo', u'netmask': 8, u'mac': u'', u'ipv4': u'127.0.0.1', u'cidrv4': u'127.0.0.1/8',
                 u'gateway': u'10.99.63.254'},
                {u'name': u'eno1', u'netmask': 19, u'mac': u'40:a8:f0:3d:ed:a0', u'ipv4': u'10.99.34.1',
                 u'cidrv4': u'10.99.34.1/19', u'gateway': u'10.99.63.254'},
                {u'name': u'eno2', u'netmask': 19, u'mac': u'40:a8:f0:3d:ed:a1', u'ipv4': u'10.99.34.1',
                 u'cidrv4': u'10.99.34.1/19', u'gateway': u'10.99.63.254'},
                {u'name': u'eno3', u'netmask': 19, u'mac': u'40:a8:f0:3d:ed:a2', u'ipv4': u'10.99.34.1',
                 u'cidrv4': u'10.99.34.1/19', u'gateway': u'10.99.63.254'},
                {u'name': u'eno4', u'netmask': 19, u'mac': u'40:a8:f0:3d:ed:a3', u'ipv4': u'10.99.34.1',
                 u'cidrv4': u'10.99.34.1/19', u'gateway': u'10.99.63.254'}
            ],
            u'ignition-journal': None
        }
        with self.smart.connected_session() as session:
            inject = crud.InjectDiscovery(session, self.ignition_journal_path, p)
            inject.commit()
            fetch = crud.FetchDiscovery(session, self.ignition_journal_path)
            fetch.get_all()

    def test_10(self):
        mac = posts.M01["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 0, 'kubernetes-node': 0, 'etcd-member': 1}
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))

        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))

        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
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
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            with self.assertRaises(LookupError):
                inject.apply_roles()

            self.assertEqual(inject.commit(), (e, False))

        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
            self.assertEqual([], fetch.get_roles_by_mac_selector(mac))

    def test_19(self):
        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
            self.assertEqual(7, len(fetch.get_schedules()))

    def test_20(self):
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": ""
            }
        }
        with self.smart.connected_session() as session:
            with self.assertRaises(AttributeError):
                crud.InjectSchedule(session, s)

    def test_21(self):
        with self.smart.connected_session() as session:
            f = crud.FetchSchedule(session)
            r = f.get_role("etcd-member")
            self.assertEqual(4, len(r))
            for i in r:
                self.assertTrue(i["as_boot"])
                self.assertEqual(str, type(i["mac"]))
                self.assertEqual(str, type(i["ipv4"]))
                self.assertEqual(str, type(i["cidrv4"]))
                self.assertEqual(str, type(i["gateway"]))
                self.assertEqual(str, type(i["name"]))
                self.assertEqual(21, int(i["netmask"]))
                self.assertEqual(str, type(i["role"]))
                self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_22(self):
        with self.smart.connected_session() as session:
            f = crud.FetchSchedule(session)
            r = f.get_role("kubernetes-node")
        self.assertEqual(3, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(str, type(i["mac"]))
            self.assertEqual(str, type(i["ipv4"]))
            self.assertEqual(str, type(i["cidrv4"]))
            self.assertEqual(str, type(i["gateway"]))
            self.assertEqual(str, type(i["name"]))
            self.assertEqual(21, int(i["netmask"]))
            self.assertEqual(str, type(i["role"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_23(self):
        with self.smart.connected_session() as session:
            f = crud.FetchSchedule(session)
            r = f.get_role("kubernetes-control-plane")
        self.assertEqual(1, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(str, type(i["mac"]))
            self.assertEqual(str, type(i["ipv4"]))
            self.assertEqual(str, type(i["cidrv4"]))
            self.assertEqual(str, type(i["gateway"]))
            self.assertEqual(str, type(i["name"]))
            self.assertEqual(21, int(i["netmask"]))
            self.assertEqual(str, type(i["role"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_24(self):
        with self.smart.connected_session() as session:
            f = crud.FetchSchedule(session)
            r = f.get_role_ip_list("etcd-member")
        self.assertEqual(4, len(r))

    def test_25(self):
        with self.smart.connected_session() as session:
            f = crud.FetchSchedule(session)
            r = f.get_role_ip_list("kubernetes-control-plane")
        self.assertEqual(1, len(r))

    def test_26(self):
        with self.smart.connected_session() as session:
            f = crud.FetchSchedule(session)
            r = f.get_role_ip_list("kubernetes-node")
        self.assertEqual(3, len(r))

    def test_27(self):
        mac = posts.M08["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-control-plane", "etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 2, 'kubernetes-node': 3, 'etcd-member': 5}
        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))

        with self.smart.connected_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        with self.smart.connected_session() as session:
            fetch = crud.FetchSchedule(session)
            self.assertEqual(["kubernetes-control-plane", "etcd-member"], fetch.get_roles_by_mac_selector(mac))
            self.assertEqual(2, len(fetch.get_roles(model.ScheduleRoles.etcd_member,
                                                    model.ScheduleRoles.kubernetes_control_plane)))

    def test_28(self):
        with self.smart.connected_session() as session:
            a = crud.FetchSchedule(session)
            self.assertEqual(16, len(a.get_available_machines()))

    def test_30(self):
        with self.smart.connected_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M01["boot-info"]["uuid"], posts.M01["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            self.assertEqual(i.mac, posts.M01["boot-info"]["mac"])

    def test_31(self):
        with self.smart.connected_session() as session:
            rq = "os=installed"
            with self.assertRaises(AttributeError):
                crud.InjectLifecycle(session, request_raw_query=rq)

    def test_32(self):
        with self.smart.connected_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M01["boot-info"]["uuid"], posts.M01["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_ignition(True)

    def test_33(self):
        with self.smart.connected_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M02["boot-info"]["uuid"], posts.M02["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_ignition(True)
            j = crud.InjectLifecycle(session, request_raw_query=rq)
            j.refresh_lifecycle_ignition(True)
        with self.smart.connected_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertTrue(f.get_ignition_uptodate_status(posts.M02["boot-info"]["mac"]))

    def test_34(self):
        with self.smart.connected_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M03["boot-info"]["uuid"], posts.M03["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_ignition(True)
        with self.smart.connected_session() as session:
            j = crud.InjectLifecycle(session, request_raw_query=rq)
            j.refresh_lifecycle_ignition(False)
        with self.smart.connected_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertFalse(f.get_ignition_uptodate_status(posts.M03["boot-info"]["mac"]))
            self.assertEqual(3, len(f.get_all_updated_status()))

    def test_35(self):
        with self.smart.connected_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M03["boot-info"]["uuid"], posts.M03["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_coreos_install(True)
        with self.smart.connected_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertTrue(f.get_coreos_install_status(posts.M03["boot-info"]["mac"]))
            self.assertEqual(1, len(f.get_all_coreos_install_status()))

    def test_36(self):
        with self.smart.connected_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M03["boot-info"]["uuid"], posts.M03["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.apply_lifecycle_rolling(True)

        with self.smart.connected_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertTrue(f.get_rolling_status(posts.M03["boot-info"]["mac"]))

        with self.smart.connected_session() as session:
            n = crud.InjectLifecycle(session, rq)
            n.apply_lifecycle_rolling(False)

        with self.smart.connected_session() as session:
            f = crud.FetchLifecycle(session)
            r = f.get_rolling_status(posts.M03["boot-info"]["mac"])
            self.assertFalse(r)

    def test_37(self):
        with self.smart.connected_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertIsNone(f.get_rolling_status(posts.M04["boot-info"]["mac"]))

    def test_38(self):
        with self.smart.connected_session() as session:
            view = crud.FetchView(session)
            result = view.get_machines()
        self.assertEqual(25, len(result))
        # Roles
        for i in result[1:]:
            roles = i[0].split(",")
            for r in roles:
                self.assertIn(r, [
                    "",
                    model.ScheduleRoles.etcd_member,
                    model.ScheduleRoles.kubernetes_control_plane,
                    model.ScheduleRoles.kubernetes_node
                ])
        # CIDR
        for i in result[1:]:
            self.assertEqual(1, i[2].count("/"))

    def test_99_healthz(self):
        for i in range(10):
            with self.smart.connected_session() as session:
                crud.health_check(session, time.time(), "unittest")
