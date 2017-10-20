import datetime
import time
import unittest

import ops
from app import configs
from app import crud
from app import model
from common import posts

ec = configs.EnjoliverConfig()


@unittest.skipIf(__name__ == "__main__", "")
class TestModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raise NotImplementedError

    @staticmethod
    def set_up_class_checks(smart):
        model.BASE.metadata.drop_all(smart.get_engine_connection())
        model.BASE.metadata.create_all(smart.get_engine_connection())
        with smart.new_session() as session:
            ops.health_check(session, time.time(), "unittest")

    # @unittest.skip("")
    def test_00(self):
        for _ in range(3):
            self.repositories.discovery.upsert(posts.M01)
            disco = self.repositories.discovery.fetch_all_discovery()
            expect = {'boot-info': {'uuid': 'b7f5f93a-b029-475f-b3a4-479ba198cb8a',
                                    'mac': '52:54:00:e8:32:5b'},
                      'disks': [{'path': '/dev/sda', 'size-bytes': 21474836480}],
                      'interfaces': [
                          {'gateway': '172.20.0.1', 'as_boot': True, 'fqdn': None, 'mac': '52:54:00:e8:32:5b',
                           'netmask': 21, 'name': 'eth0', 'cidrv4': '172.20.0.65/21', 'ipv4': '172.20.0.65'}]}
            self.assertEqual(1, len(disco))
            machine = disco[0]
            self.assertEqual(expect["boot-info"]["uuid"], machine["boot-info"]["uuid"])
            self.assertEqual(expect["boot-info"]["mac"], machine["boot-info"]["mac"])
            self.assertListEqual(expect["interfaces"], machine["interfaces"])
            self.assertListEqual(expect["disks"], machine["disks"])

    def test_01(self):
        for _ in range(3):
            self.repositories.discovery.upsert(posts.M02)
            disco = self.repositories.discovery.fetch_all_discovery()
            self.assertEqual(2, len(disco))
            disco.sort(key=lambda x: x["boot-info"]["created-date"])
            expects = [{'boot-info': {'uuid': 'b7f5f93a-b029-475f-b3a4-479ba198cb8a',
                                      'mac': '52:54:00:e8:32:5b'},
                        'disks': [{'path': '/dev/sda', 'size-bytes': 21474836480}],
                        'interfaces': [
                            {'gateway': '172.20.0.1', 'as_boot': True, 'fqdn': None, 'mac': '52:54:00:e8:32:5b',
                             'netmask': 21, 'name': 'eth0', 'cidrv4': '172.20.0.65/21', 'ipv4': '172.20.0.65'}]},
                       {'boot-info': {
                           'mac': '52:54:00:a5:24:f5', 'uuid': 'a21a9123-302d-488d-976c-5d6ded84a32d',
                       },
                           'interfaces': [
                               {'gateway': '172.20.0.1', 'fqdn': None, 'ipv4': '172.20.0.51', 'name': 'eth0',
                                'as_boot': True,
                                'mac': '52:54:00:a5:24:f5', 'cidrv4': '172.20.0.51/21', 'netmask': 21}],
                           'disks': [{'size-bytes': 21474836480, 'path': '/dev/sda'}]}
                       ]
            for i, expect in enumerate(expects):
                machine = disco[i]
                self.assertEqual(expect["boot-info"]["uuid"], machine["boot-info"]["uuid"])
                self.assertEqual(expect["boot-info"]["mac"], machine["boot-info"]["mac"])
                self.assertListEqual(expect["interfaces"], machine["interfaces"])
                self.assertListEqual(expect["disks"], machine["disks"])

    def test_03(self):
        for m in posts.ALL:
            self.repositories.discovery.upsert(m)
        disco = self.repositories.discovery.fetch_all_discovery()
        self.assertEqual(len(posts.ALL), len(disco))

    def test_10(self):
        mac = posts.M01["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 0, 'kubernetes-node': 0, 'etcd-member': 1}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))

        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        e = self.repositories.machine_schedule.get_all_schedules()
        self.assertEqual({mac: [u"etcd-member"]}, e)
        self.assertEqual([u"etcd-member"], self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_11(self):
        mac = posts.M02["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 0, 'kubernetes-node': 0, 'etcd-member': 2}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        self.assertEqual([u"etcd-member"], self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_12(self):
        mac = posts.M03["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 0, 'kubernetes-node': 0, 'etcd-member': 3}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))

        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        self.repositories.machine_schedule.get_roles_by_mac_selector(mac)

    def test_13(self):
        mac = posts.M04["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-control-plane"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 0, 'etcd-member': 3}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        self.assertEqual([u"kubernetes-control-plane"],
                         self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_14(self):
        mac = posts.M04["boot-info"]["mac"]
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 0, 'etcd-member': 4}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        self.assertEqual([u"kubernetes-control-plane", "etcd-member"], self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_15(self):
        mac = posts.M05["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-node"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 1, 'etcd-member': 4}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))

        self.assertEqual(["kubernetes-node"], self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_16(self):
        mac = posts.M06["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-node"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 2, 'etcd-member': 4}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        self.assertEqual(["kubernetes-node"], self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_17(self):
        mac = posts.M07["boot-info"]["mac"]
        s = {
            "roles": ["kubernetes-node"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 3, 'etcd-member': 4}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        self.assertEqual(["kubernetes-node"], self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_18(self):
        mac = posts.M08["boot-info"]["mac"]
        s = {
            "roles": ["bad-role"],
            "selector": {
                "mac": mac
            }
        }
        e = {'kubernetes-control-plane': 1, 'kubernetes-node': 3, 'etcd-member': 4}
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            with self.assertRaises(LookupError):
                inject.apply_roles()

            self.assertEqual(inject.commit(), (e, False))

        self.assertEqual([], self.repositories.machine_schedule.get_roles_by_mac_selector(mac))

    def test_19(self):
        self.assertEqual(7, len(self.repositories.machine_schedule.get_all_schedules()))

    def test_20(self):
        s = {
            "roles": ["etcd-member"],
            "selector": {
                "mac": ""
            }
        }
        with self.smart.new_session() as session:
            with self.assertRaises(AttributeError):
                crud.InjectSchedule(session, s)

    def test_21(self):
        r = self.repositories.machine_schedule.get_machines_by_role("etcd-member")
        self.assertEqual(4, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(str, type(i["mac"]))
            self.assertEqual(str, type(i["ipv4"]))
            self.assertEqual(str, type(i["cidrv4"]))
            self.assertEqual(str, type(i["gateway"]))
            self.assertEqual(str, type(i["name"]))
            self.assertEqual(21, int(i["netmask"]))
            self.assertEqual(str, type(i["roles"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_22(self):
        r = self.repositories.machine_schedule.get_machines_by_role("kubernetes-node")
        self.assertEqual(3, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(str, type(i["mac"]))
            self.assertEqual(str, type(i["ipv4"]))
            self.assertEqual(str, type(i["cidrv4"]))
            self.assertEqual(str, type(i["gateway"]))
            self.assertEqual(str, type(i["name"]))
            self.assertEqual(21, int(i["netmask"]))
            self.assertEqual(str, type(i["roles"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

            self.assertEqual(["kubernetes-node"], self.repositories.machine_schedule.get_roles_by_mac_selector(i["mac"]))
            with self.smart.new_session() as session:
                fetch = crud.FetchSchedule(session)
                r = fetch.get_machines_by_roles(
                    model.ScheduleRoles.etcd_member, model.ScheduleRoles.kubernetes_control_plane)
                self.assertEqual(1, len(r))

    def test_23a(self):
        r = self.repositories.machine_schedule.get_machines_by_role("kubernetes-control-plane")
        self.assertEqual(1, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(str, type(i["mac"]))
            self.assertEqual(str, type(i["ipv4"]))
            self.assertEqual(str, type(i["cidrv4"]))
            self.assertEqual(str, type(i["gateway"]))
            self.assertEqual(str, type(i["name"]))
            self.assertEqual(21, int(i["netmask"]))
            self.assertEqual(str, type(i["roles"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_23b(self):
        r = self.repositories.machine_schedule.get_machines_by_roles("kubernetes-control-plane")
        self.assertEqual(1, len(r))
        for i in r:
            self.assertTrue(i["as_boot"])
            self.assertEqual(str, type(i["mac"]))
            self.assertEqual(str, type(i["ipv4"]))
            self.assertEqual(str, type(i["cidrv4"]))
            self.assertEqual(str, type(i["gateway"]))
            self.assertEqual(str, type(i["name"]))
            self.assertEqual(21, int(i["netmask"]))
            self.assertEqual(datetime.datetime, type(i["created_date"]))

    def test_24(self):
        r = self.repositories.machine_schedule.get_role_ip_list("etcd-member")
        self.assertEqual(4, len(r))

    def test_25(self):
        r = self.repositories.machine_schedule.get_role_ip_list("kubernetes-control-plane")
        self.assertEqual(1, len(r))

    def test_26(self):
        r = self.repositories.machine_schedule.get_role_ip_list("kubernetes-node")
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
        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, True))

        with self.smart.new_session() as session:
            inject = crud.InjectSchedule(session, s)
            inject.apply_roles()
            self.assertEqual(inject.commit(), (e, False))
        with self.smart.new_session() as session:
            fetch = crud.FetchSchedule(session)
            self.assertEqual(["kubernetes-control-plane", "etcd-member"], fetch.get_roles_by_mac_selector(mac))
            r = fetch.get_machines_by_roles(
                model.ScheduleRoles.etcd_member, model.ScheduleRoles.kubernetes_control_plane)
        self.assertEqual(2, len(r))

    def test_28(self):
        self.assertEqual(15, len(self.repositories.machine_schedule.get_available_machines()))

    def test_30(self):
        with self.smart.new_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M01["boot-info"]["uuid"], posts.M01["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            self.assertEqual(i.mac, posts.M01["boot-info"]["mac"])

    def test_31(self):
        with self.smart.new_session() as session:
            rq = "os=installed"
            with self.assertRaises(AttributeError):
                crud.InjectLifecycle(session, request_raw_query=rq)

    def test_32(self):
        with self.smart.new_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M01["boot-info"]["uuid"], posts.M01["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_ignition(True)

    def test_33(self):
        with self.smart.new_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M02["boot-info"]["uuid"], posts.M02["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_ignition(True)
            j = crud.InjectLifecycle(session, request_raw_query=rq)
            j.refresh_lifecycle_ignition(True)
        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertTrue(f.get_ignition_uptodate_status(posts.M02["boot-info"]["mac"]))

    def test_34(self):
        with self.smart.new_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M03["boot-info"]["uuid"], posts.M03["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_ignition(True)
        with self.smart.new_session() as session:
            j = crud.InjectLifecycle(session, request_raw_query=rq)
            j.refresh_lifecycle_ignition(False)
        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertFalse(f.get_ignition_uptodate_status(posts.M03["boot-info"]["mac"]))
            self.assertEqual(3, len(f.get_all_updated_status()))

    def test_35(self):
        with self.smart.new_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M03["boot-info"]["uuid"], posts.M03["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.refresh_lifecycle_coreos_install(True)
        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            self.assertTrue(f.get_coreos_install_status(posts.M03["boot-info"]["mac"]))
            self.assertEqual(1, len(f.get_all_coreos_install_status()))

    def test_36(self):
        with self.smart.new_session() as session:
            rq = "uuid=%s&mac=%s&os=installed" % (posts.M03["boot-info"]["uuid"], posts.M03["boot-info"]["mac"])
            i = crud.InjectLifecycle(session, request_raw_query=rq)
            i.apply_lifecycle_rolling(True)

        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            status = f.get_rolling_status(posts.M03["boot-info"]["mac"])
            self.assertTrue(status[0])
            self.assertEqual("kexec", status[1])

        with self.smart.new_session() as session:
            n = crud.InjectLifecycle(session, rq)
            n.apply_lifecycle_rolling(False)

        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            r = f.get_rolling_status(posts.M03["boot-info"]["mac"])
            self.assertFalse(r[0])
            self.assertEqual("kexec", r[1])

        with self.smart.new_session() as session:
            n = crud.InjectLifecycle(session, rq)
            n.apply_lifecycle_rolling(True, "reboot")

        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            r = f.get_rolling_status(posts.M03["boot-info"]["mac"])
            self.assertTrue(r[0])
            self.assertEqual("reboot", r[1])

        with self.smart.new_session() as session:
            n = crud.InjectLifecycle(session, rq)
            n.apply_lifecycle_rolling(True, "poweroff")

        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            r = f.get_rolling_status(posts.M03["boot-info"]["mac"])
            self.assertTrue(r[0])
            self.assertEqual("poweroff", r[1])

        with self.smart.new_session() as session:
            n = crud.InjectLifecycle(session, rq)
            with self.assertRaises(LookupError):
                n.apply_lifecycle_rolling(True, "notpossible")

        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            r = f.get_rolling_status(posts.M03["boot-info"]["mac"])
            self.assertTrue(r[0])
            self.assertEqual("poweroff", r[1])

    def test_37(self):
        with self.smart.new_session() as session:
            f = crud.FetchLifecycle(session)
            t = f.get_rolling_status(posts.M04["boot-info"]["mac"])
            self.assertIsNone(t[0])
            self.assertIsNone(t[1])
            r = f.get_all_rolling_status()
            self.assertEqual(1, len(r))

    def test_39(self):
        with self.smart.new_session() as session:
            export = crud.BackupExport(session)
            playbook = export.get_playbook()
            self.assertEqual(10, len(playbook))
        for i, entry in enumerate(playbook):
            if i % 2 == 0:
                lastest = entry["data"]["boot-info"]["mac"]
            else:
                check = entry["data"]["selector"]["mac"]

    def test_99_healthz(self):
        for i in range(10):
            with self.smart.new_session() as session:
                ops.health_check(session, time.time(), "unittest")

        with self.smart.new_session() as session:
            ops.health_check_purge(session)

        with self.smart.new_session() as session:
            ops.health_check_purge(session)
