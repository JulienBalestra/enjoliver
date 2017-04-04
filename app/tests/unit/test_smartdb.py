import unittest

import os

from app import configs
from app import smartdb

ec = configs.EnjoliverConfig()


class TestModel(unittest.TestCase):
    unit_path = os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        if os.path.isfile(ec.db_path):
            os.remove(ec.db_path)

        smartdb.SmartClient.engines = []

    # @unittest.skip("")
    def test_00(self):
        ss = smartdb.SmartClient("sqlite:////var/lib/enjoliver/enjoliver.sqlite")
        self.assertEqual(smartdb._SingleEndpoint, type(ss))
        self.assertEqual(1, len(ss.engines))

    def test_01(self):
        ss = smartdb.SmartClient("cockroachdb://root@localhost:26257")
        self.assertEqual(smartdb._SingleEndpoint, type(ss))
        self.assertEqual(1, len(ss.engines))

    def test_02(self):
        ss = smartdb.SmartClient(
            "cockroachdb://root@1.1.1.1:26257,cockroachdb://root@1.1.1.2:26257,cockroachdb://root@1.1.1.3:26257")
        self.assertEqual(smartdb._MultipleEndpoints, type(ss))
        self.assertEqual(3, len(ss.engines))

    def test_03(self):
        ss = smartdb.SmartClient("sqlite:///%s/dbs/smart.sqlite" % (self.unit_path))
        self.assertEqual(smartdb._SingleEndpoint, type(ss))
        self.assertEqual(1, len(ss.engines))
        ss.create_base()
        ss.connected_cockroach_session()

    def test_04(self):
        ss = smartdb.SmartClient("cockroachdb://root@127.0.0.1:16257")
        self.assertEqual(smartdb._SingleEndpoint, type(ss))
        self.assertEqual(1, len(ss.engines))
        with self.assertRaises(ConnectionError):
            with ss.connected_cockroach_session() as session:
                pass
        with ss.new_session() as session:
            pass

    def test_05(self):
        ss = smartdb.SmartClient("cockroachdb://root@127.0.0.1:16257,cockroachdb://root@127.0.1.1:16257")
        self.assertEqual(smartdb._MultipleEndpoints, type(ss))
        self.assertEqual(2, len(ss.engines))
        with self.assertRaises(ConnectionError):
            with ss.new_session() as session:
                pass
