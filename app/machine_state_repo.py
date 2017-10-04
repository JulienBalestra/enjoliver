import datetime
import logging

import smartdb
from model import MachineCurrentState, MachineInterface

logger = logging.getLogger(__file__)


class MachineStateRepository:
    def __init__(self, smart: smartdb.SmartDatabaseClient):
        self.smart = smart

    def _update_state(self, machine_current_state: MachineCurrentState):
        @smartdb.cockroach_transaction
        def callback(caller=self._update_state.__name__):
            with self.smart.new_session() as session:
                session.add(machine_current_state)
                session.commit()

        try:
            callback(self._update_state.__name__)
        except Exception as e:
            # updating state is not critical so we accept to wide catch all exception and pass over it just with a log
            logger.error("fail to update machine with mac: %s with state %s: %s" % (
                machine_current_state.machine_mac, machine_current_state.state_name, e))

    def fetch(self, finished_in_less_than_min: int):
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(minutes=finished_in_less_than_min)
        results = []
        with self.smart.new_session() as session:
            for row in session.execute("""SELECT mi.fqdn, mcs.machine_mac, mcs.state_name, mcs.updated_date FROM 'machine-current-state' as mcs
            LEFT JOIN 'machine-interface' AS mi ON mi.machine_id = mcs.machine_id
            WHERE mcs.updated_date >= :date""", {"date": time_limit}):
                results.append({
                    "fqdn": row[0],
                    "mac": row[1],
                    "state": row[2],
                    "date": row[3]
                })
            return results

    def update(self, mac: str, state: str):
        with self.smart.new_session() as session:
            state_machine = session.query(MachineCurrentState).filter(
                MachineCurrentState.machine_mac == mac).first()

            machine = session.query(MachineInterface).filter(MachineInterface.mac == mac).first()

        machine_id = None if not machine else machine.id
        now = datetime.datetime.utcnow()

        if not state_machine:
            logger.debug(
                "machine with mac: %s doesn't exist in table %s: creating with state %s" % (
                    mac, MachineCurrentState.__tablename__, state))
            self._update_state(
                MachineCurrentState(
                    machine_id=machine_id,
                    state_name=state,
                    machine_mac=mac,
                    created_date=now,
                    updated_date=now, )
            )
        else:
            state_machine.state_name = state
            state_machine.machine_id = machine_id
            state_machine.updated_date = now
            self._update_state(state_machine)
