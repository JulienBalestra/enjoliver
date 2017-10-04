import unittest

import copy

from app import user_interface_repo, smartdb, model
from model import MachineCurrentState, MachineInterface, Machine, MachineStates, MachineDisk


class TestMachineStateRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_uri = 'sqlite:///:memory:'

        cls.smart = smartdb.SmartDatabaseClient(db_uri)

    def setUp(self):
        model.BASE.metadata.drop_all(self.smart.get_engine_connection())
        model.BASE.metadata.create_all(self.smart.get_engine_connection())

    def test_empty(self):
        ui = user_interface_repo.UserInterfaceRepository(self.smart)
        self.assertEqual(ui.vuejs_data, ui.get_machines_overview())

    def test_one_machine_with_only_interfaces(self):
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

        expect = copy.deepcopy(user_interface_repo.UserInterfaceRepository.vuejs_data)
        expect["gridData"] = [
            {
                'CIDR': '127.0.0.1/8',
                'LastReport': None,
                'UpdateStrategy': 'Disable',
                'LastChange': None,
                'MAC': '00:00:00:00:00:00',
                'UpToDate': None,
                'FQDN': None,
                'DiskProfile': 'inMemory',
                'LastState': None,
                'Roles': ''}
        ]
        ui = user_interface_repo.UserInterfaceRepository(self.smart)
        self.assertEqual(expect, ui.get_machines_overview())

    def test_one_machine_full(self):
        mac = "00:00:00:00:00:00"

        with self.smart.new_session() as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(
                MachineDisk(path="/dev/sda", size=1024 * 1024 * 1024, machine_id=machine_id)
            )
            session.add(
                MachineCurrentState(machine_id=machine_id, machine_mac=mac, state_name=MachineStates.discovery)
            )
            session.commit()

        expect = copy.deepcopy(user_interface_repo.UserInterfaceRepository.vuejs_data)
        expect["gridData"] = [
            {
                'CIDR': '127.0.0.1/8',
                'LastReport': None,
                'UpdateStrategy': 'Disable',
                'LastChange': None,
                'MAC': '00:00:00:00:00:00',
                'UpToDate': None,
                'FQDN': None,
                'DiskProfile': 'S',
                'LastState': MachineStates.discovery,
                'Roles': ''}
        ]
        ui = user_interface_repo.UserInterfaceRepository(self.smart)
        data = ui.get_machines_overview()
        self.assertEqual(expect, data)
