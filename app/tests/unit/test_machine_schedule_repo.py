import unittest

import posts
from app import smartdb, model
from model import MachineInterface, Machine
from repositories.machine_discovery_repo import DiscoveryRepository
from repositories.machine_schedule_repo import ScheduleRepository


class TestMachineScheduleRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_uri = 'sqlite:///:memory:'

        cls.smart = smartdb.SmartDatabaseClient(db_uri)

    def setUp(self):
        model.BASE.metadata.drop_all(self.smart.get_engine_connection())
        model.BASE.metadata.create_all(self.smart.get_engine_connection())

    def test_one_machine(self):
        mac = "00:00:00:00:00:00"
        with self.smart.new_session() as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.commit()

        ms = ScheduleRepository(self.smart)
        ret = ms.get_available_machines()
        self.assertEqual(1, len(ret))

    def test_one_machine_discovery(self):
        mds = DiscoveryRepository(self.smart)
        mds.upsert(posts.M01)
        ms = ScheduleRepository(self.smart)
        ret = ms.get_available_machines()
        self.assertEqual(1, len(ret))

    def test_two_machine_discovery(self):
        mds = DiscoveryRepository(self.smart)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = ScheduleRepository(self.smart)
        ret = ms.get_available_machines()
        self.assertEqual(2, len(ret))

    def test_two_machine_discovery_idemp(self):
        mds = DiscoveryRepository(self.smart)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = ScheduleRepository(self.smart)
        ret = ms.get_available_machines()
        self.assertEqual(2, len(ret))
        ms = ScheduleRepository(self.smart)
        ret = ms.get_available_machines()
        self.assertEqual(2, len(ret))

    def test_machine_without_role(self):
        mds = DiscoveryRepository(self.smart)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = ScheduleRepository(self.smart)
        for role in model.ScheduleRoles.roles:
            ret = ms.get_machines_by_role(role)
            self.assertEqual(0, len(ret))

    def test_machine_without_role2(self):
        mds = DiscoveryRepository(self.smart)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = ScheduleRepository(self.smart)
        ret = ms.get_all_schedules()
        self.assertEqual(0, len(ret))

    def test_machine_without_role3(self):
        mds = DiscoveryRepository(self.smart)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = ScheduleRepository(self.smart)
        ret = ms.get_roles_by_mac_selector(posts.M01["boot-info"]["mac"])
        self.assertEqual(0, len(ret))


