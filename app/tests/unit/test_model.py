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
        fetch = crud.Fetch(cls.engine, cls.ignition_journal_path)
        assert fetch.get_all_interfaces() == []
        assert fetch.get_all() == []
        assert fetch.get_ignition_journal("") == []
        assert fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"]) == []

    # @unittest.skip("")
    def test_00(self):
        i = crud.Inject(self.engine, self.ignition_journal_path, posts.M01)
        i.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
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
                'cidrv4': u'172.20.0.65/21'
            }
        ], interfaces)
        journal = fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"])
        fetch.close()
        self.assertEqual(len(journal), len(posts.M01["ignition-journal"]))

    # @unittest.skip("")
    def test_00_1(self):
        i = crud.Inject(self.engine, self.ignition_journal_path, posts.M01)
        i.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
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
                'cidrv4': u'172.20.0.65/21'
            }
        ], interfaces)
        journal = fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"])
        fetch.close()
        self.assertEqual(len(journal), len(posts.M01["ignition-journal"]))

    def test_01(self):
        i = crud.Inject(self.engine, self.ignition_journal_path, posts.M02)
        i.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
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
                'ipv4': u'172.20.0.65'
            },
            {
                'machine': u'a21a9123-302d-488d-976c-5d6ded84a32d',
                'mac': u'52:54:00:a5:24:f5',
                'name': u'eth0',
                'cidrv4': u'172.20.0.51/21',
                'as_boot': True,
                'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
                'netmask': 21,
                'ipv4': u'172.20.0.51'
            }
        ], interfaces)
        fetch.close()

    def test_02(self):
        m1 = crud.Inject(self.engine, self.ignition_journal_path, posts.M01)
        m1.commit_and_close()
        i = crud.Inject(self.engine, self.ignition_journal_path, posts.M02)
        i.commit_and_close()
        i = crud.Inject(self.engine, self.ignition_journal_path, posts.M02)
        i.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(interfaces), 2)
        self.assertEqual(len(fetch.get_ignition_journal(posts.M02["boot-info"]["uuid"])), 39)
        self.assertEqual([
            {'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a', 'mac': u'52:54:00:e8:32:5b', 'name': u'eth0',
             'cidrv4': u'172.20.0.65/21', 'as_boot': True, 'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             'netmask': 21, 'ipv4': u'172.20.0.65'},
            {'machine': u'a21a9123-302d-488d-976c-5d6ded84a32d', 'mac': u'52:54:00:a5:24:f5', 'name': u'eth0',
             'cidrv4': u'172.20.0.51/21', 'as_boot': True, 'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             'netmask': 21, 'ipv4': u'172.20.0.51'}
        ], interfaces)
        fetch.close()

    def test_03(self):
        i = crud.Inject(self.engine, self.ignition_journal_path, posts.M03)
        i.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(interfaces), 3)
        self.assertEqual(len(fetch.get_ignition_journal(posts.M03["boot-info"]["uuid"])), 39)

    def test_04(self):
        for p in posts.ALL:
            i = crud.Inject(self.engine, self.ignition_journal_path, p)
            i.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))

    def test_05(self):
        for p in posts.ALL:
            i = crud.Inject(self.engine, self.ignition_journal_path, p)
            i.commit_and_close()

        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))

    def test_06(self):
        i = crud.Inject(self.engine, self.ignition_journal_path, posts.M16)
        i.commit_and_close()

    def test_07(self):
        with self.assertRaises(KeyError):
            i = crud.Inject(self.engine, self.ignition_journal_path, {
                u'boot-info': {},
                u'lldp': {},
                u'interfaces': []
            })
            i.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))
        machines = fetch.get_all()

        self.assertEqual(len(posts.ALL), len(fetch.get_all()))
        line_nb = 0
        for m in machines:
            line_nb += len(fetch.get_ignition_journal(m["boot-info"]["uuid"]))

        self.assertEqual(587, line_nb)

    def test_08(self):
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
        all_data = fetch.get_all_interfaces()
        chassis_names = [k["chassis_name"] for k in all_data]
        self.assertEqual(4, chassis_names.count(None))
        self.assertEqual(19, chassis_names.count("rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4"))

    def test_09(self):
        inject = crud.Inject(self.engine, self.ignition_journal_path, posts.M01)
        inject.commit_and_close()
        fetch = crud.Fetch(self.engine, self.ignition_journal_path)
        all_data_new = fetch.get_all()
        self.assertEqual(all_data_new[0]["boot-info"]["uuid"], posts.M01["boot-info"]["uuid"])
