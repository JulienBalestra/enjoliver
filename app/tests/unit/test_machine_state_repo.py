import unittest

from app import smartdb, model
from model import MachineCurrentState, MachineInterface, Machine, MachineStates
from repositories import machine_state_repo


class TestMachineStateRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_uri = 'sqlite:///:memory:'

        cls.smart = smartdb.SmartDatabaseClient(db_uri)

    def setUp(self):
        model.BASE.metadata.drop_all(self.smart.get_engine_connection())
        model.BASE.metadata.create_all(self.smart.get_engine_connection())

    def test_no_machine_no_state(self):
        mac = "00:00:00:00:00:00"
        state = MachineStates.booting
        msr = machine_state_repo.MachineStateRepository(self.smart)
        msr.update(mac, state)

        with self.smart.new_session() as session:
            res = session.query(MachineCurrentState).filter(MachineCurrentState.machine_mac == mac).first()
            self.assertEqual(mac, res.machine_mac)
            self.assertEqual(state, res.state_name)
            self.assertEqual(None, res.machine_id)

    def test_machine_exists_no_state(self):
        mac = "00:00:00:00:00:00"
        state = MachineStates.booting

        with self.smart.new_session() as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.commit()

        msr = machine_state_repo.MachineStateRepository(self.smart)
        msr.update(mac, state)

        with self.smart.new_session() as session:
            res = session.query(MachineCurrentState).filter(MachineCurrentState.machine_mac == mac).first()
            self.assertEqual(mac, res.machine_mac)
            self.assertEqual(state, res.state_name)
            self.assertEqual(machine_id, res.machine_id)

    def test_machine_exists_state_exists(self):
        mac = "00:00:00:00:00:00"
        state = MachineStates.booting
        msr = machine_state_repo.MachineStateRepository(self.smart)

        with self.smart.new_session() as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.commit()

        msr.update(mac, state)
        new_state = MachineStates.discovery
        msr.update(mac, new_state)

        with self.smart.new_session() as session:
            res = session.query(MachineCurrentState).filter(MachineCurrentState.machine_mac == mac).first()
            self.assertEqual(mac, res.machine_mac)
            self.assertEqual(new_state, res.state_name)
            self.assertEqual(machine_id, res.machine_id)

        ret = msr.fetch(10)
        self.assertEqual([{
            "fqdn": None,
            "mac": mac,
            "state": new_state,
            "date": res.updated_date
        }], ret)
