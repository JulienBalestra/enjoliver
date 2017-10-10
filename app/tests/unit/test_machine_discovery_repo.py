import copy
import unittest

from app import smartdb, model
from common import posts
from model import MachineInterface, Machine, MachineDisk, Chassis, ChassisPort
from repositories.machine_discovery_repo import DiscoveryRepository


class TestMachineStateRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_uri = 'sqlite:///:memory:'

        cls.smart = smartdb.SmartDatabaseClient(db_uri)

    def setUp(self):
        model.BASE.metadata.drop_all(self.smart.get_engine_connection())
        model.BASE.metadata.create_all(self.smart.get_engine_connection())

    def test_bad_content(self):
        mdr = DiscoveryRepository(self.smart)
        with self.assertRaises(TypeError):
            mdr.upsert(dict())
        with self.assertRaises(TypeError):
            mdr.upsert({"lldp": ""})

    def test_no_machine(self):
        mdr = DiscoveryRepository(self.smart)
        mdr.upsert(posts.M01)

        with self.smart.new_session() as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(1, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

    def test_no_machine_readd_same(self):
        mdr = DiscoveryRepository(self.smart)

        for i in range(3):
            mdr.upsert(posts.M01)

            with self.smart.new_session() as session:
                self.assertEqual(1, session.query(Machine).count())
                self.assertEqual(1, session.query(MachineInterface).count())
                self.assertEqual(1, session.query(MachineDisk).count())
                self.assertEqual(1, session.query(Chassis).count())
                self.assertEqual(1, session.query(ChassisPort).count())

    def test_no_machine_readd_disk_diff(self):
        mdr = DiscoveryRepository(self.smart)
        mdr.upsert(posts.M01)

        with self.smart.new_session() as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(1, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

        with_new_disk = copy.deepcopy(posts.M01)
        with_new_disk["disks"].append({'size-bytes': 21474836481, 'path': '/dev/sdb'})
        mdr.upsert(with_new_disk)

        with self.smart.new_session() as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(2, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

    def test_no_machine_remove_disks(self):
        mdr = DiscoveryRepository(self.smart)
        mdr.upsert(posts.M01)

        with self.smart.new_session() as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(1, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

        without_disks = copy.deepcopy(posts.M01)
        without_disks["disks"] = None
        mdr.upsert(without_disks)

        with self.smart.new_session() as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(0, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

    def test_fetch_one_machine(self):
        mdr = DiscoveryRepository(self.smart)
        mdr.upsert(posts.M01)

        disco = mdr.fetch_all_discovery()
        self.assertEqual(1, len(disco))
        self.assertEqual(posts.M01["boot-info"]["mac"], disco[0]["boot-info"]["mac"])
        self.assertEqual(posts.M01["boot-info"]["uuid"], disco[0]["boot-info"]["uuid"])
        self.assertEqual(posts.M01["disks"], disco[0]["disks"])
        self.assertEqual(1, len(disco[0]["interfaces"]))
        self.assertEqual(posts.M01["boot-info"]["mac"], disco[0]["interfaces"][0]["mac"])
        self.assertTrue(disco[0]["interfaces"][0]["as_boot"])

