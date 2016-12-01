import os
import unittest

from sqlalchemy import create_engine

import crud
import model
from common import posts


class TestModel(unittest.TestCase):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path
    engine = None

    @classmethod
    def setUpClass(cls):
        db = "%s/%s.sqlite" % (cls.dbs_path, TestModel.__name__.lower())
        try:
            os.remove(db)
        except OSError:
            pass
        cls.engine = create_engine('sqlite:///%s' % db)
        model.Base.metadata.create_all(cls.engine)

    def test_00(self):
        i = crud.Inject(self.engine, posts.M01)
        i.commit()
        fetch = crud.Fetch(self.engine)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual([
            {'name': u'eth0',
             'as_boot': True,
             'netmask': 21,
             'mac': u'52:54:00:e8:32:5b',
             'ipv4': u'172.20.0.65',
             'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a',
             'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             'cidrv4': u'172.20.0.65/21'}
        ], interfaces)

    def test_01(self):
        i = crud.Inject(self.engine, posts.M02)
        i.commit()
        i = crud.Inject(self.engine, posts.M02)
        i.commit()
        fetch = crud.Fetch(self.engine)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(interfaces), 2)
        self.assertEqual(len(fetch.get_ignition_journal(posts.M01["boot-info"]["uuid"])), 39)

    def test_02(self):
        for p in posts.ALL:
            i = crud.Inject(self.engine, p)
            i.commit()
        fetch = crud.Fetch(self.engine)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))
        # print fetch.get_all_interfaces()

    def test_03(self):
        for p in posts.ALL:
            i = crud.Inject(self.engine, p)
            i.commit()

        fetch = crud.Fetch(self.engine)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))

    def test_04(self):
        i = crud.Inject(self.engine, posts.M16)
        i.commit()

    def test_05(self):
        with self.assertRaises(KeyError):
            i = crud.Inject(self.engine, {
                u'boot-info': {},
                u'lldp': {},
                u'interfaces': []
            })
            i.commit()
        fetch = crud.Fetch(self.engine)
        interfaces = fetch.get_all_interfaces()
        self.assertEqual(len(posts.ALL), len(interfaces))
        machines = fetch.get_all()

        self.assertEqual(len(posts.ALL), len(fetch.get_all()))
        line_nb = 0
        for m in machines:
            line_nb += len(fetch.get_ignition_journal(m["boot-info"]["uuid"]))

        self.assertEqual(587, line_nb)
