import logging

from sqlalchemy.orm import joinedload

import smartdb
from model import Machine, Schedule, MachineInterface

logger = logging.getLogger(__file__)


class ScheduleRepository:
    __name__ = "ScheduleRepository"

    def __init__(self, smart: smartdb.SmartDatabaseClient):
        self.smart = smart

    @staticmethod
    def _lint_schedule_data(schedule_data: dict):
        # {
        #     "roles": ["kubernetes-control-plane", "etcd-member"],
        #     "selector": {
        #         "mac": mac
        #     }
        # }
        try:
            _ = schedule_data["selector"]["mac"]
            _ = schedule_data["roles"]
        except KeyError as e:
            err_msg = "missing keys in schedule data: '%s'" % e
            logger.error(err_msg)
            raise TypeError(err_msg)

        return schedule_data

    def create_schedule(self, schedule_data: dict):
        caller = "%s.%s" % (self.__name__, self.create_schedule.__name__)
        schedule_data = self._lint_schedule_data(schedule_data)

        @smartdb.cockroach_transaction
        def callback(caller=caller):
            commit = False
            with self.smart.new_session() as session:
                machine = session.query(Machine) \
                    .join(MachineInterface) \
                    .options(joinedload("schedules")) \
                    .filter(MachineInterface.mac == schedule_data["selector"]["mac"]) \
                    .first()

                if not machine:
                    logger.error("machine mac %s not in db", schedule_data["selector"]["mac"])
                    return commit
                else:
                    machine_already_scheduled = [s.role for s in machine.schedules]
                    for role in schedule_data["roles"]:
                        if role in machine_already_scheduled:
                            logger.info("machine mac %s already scheduled with role %s",
                                        schedule_data["selector"]["mac"], role)
                            continue
                        session.add(Schedule(machine_id=machine.id, role=role))
                        logger.info("scheduling machine mac %s as role %s", schedule_data["selector"]["mac"], role)
                        commit = True

                    session.commit() if commit else None

            return commit

        return callback(caller)

    def get_all_schedules(self):
        result = dict()
        with self.smart.new_session() as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("schedules")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True):
                if machine.schedules:
                    result[machine.interfaces[0].mac] = [k.role for k in machine.schedules]

        return result

    def get_roles_by_mac_selector(self, mac: str):
        result = []
        with self.smart.new_session() as session:
            for s in session.query(Schedule) \
                    .join(Machine) \
                    .join(MachineInterface) \
                    .filter(MachineInterface.mac == mac):
                result.append(s.role)

        return result

    def get_available_machines(self):
        available_machines = []
        with self.smart.new_session() as session:
            for m in session.query(Machine) \
                    .join(MachineInterface) \
                    .options(joinedload("schedules")) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .filter(MachineInterface.as_boot == True):
                # TODO find a way to support cockroach and SQLite without this if
                if not m.schedules:
                    available_machines.append({
                        "mac": m.interfaces[0].mac,
                        "ipv4": m.interfaces[0].ipv4,
                        "cidrv4": m.interfaces[0].cidrv4,
                        "as_boot": m.interfaces[0].as_boot,
                        "name": m.interfaces[0].name,
                        "fqdn": m.interfaces[0].fqdn,
                        "netmask": m.interfaces[0].netmask,
                        "created_date": m.created_date,
                        "disks": [{"path": k.path, "size-bytes": k.size} for k in m.disks],
                    })

        return available_machines

    def _construct_machine_dict(self, machine: Machine, role):
        return {
            "mac": machine.interfaces[0].mac,
            "ipv4": machine.interfaces[0].ipv4,
            "cidrv4": machine.interfaces[0].cidrv4,
            "gateway": machine.interfaces[0].gateway,
            "as_boot": machine.interfaces[0].as_boot,
            "name": machine.interfaces[0].name,
            "netmask": machine.interfaces[0].netmask,
            "roles": role,
            "created_date": machine.created_date,
            "fqdn": machine.interfaces[0].fqdn,
            "disks": [{"path": k.path, "size-bytes": k.size} for k in machine.disks],
        }

    def get_machines_by_role(self, role: str):
        machines = []
        with self.smart.new_session() as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True) \
                    .filter(Schedule.role == role):
                machines.append(self._construct_machine_dict(machine, role))

        return machines

    def get_machines_by_roles(self, *roles):
        if len(roles) == 1:
            return self.get_machines_by_role(roles[0])
        machines = []
        roles = list(roles)

        with self.smart.new_session() as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True):
                # TODO Maybe do this with a sqlalchemy filter func
                if len(roles) == len(roles) and set(k.role for k in machine.schedules) == set(roles):
                    machines.append(self._construct_machine_dict(machine, roles))

        return machines

    def get_role_ip_list(self, role: str):
        ips = []
        with self.smart.new_session() as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .join(MachineInterface) \
                    .join(Schedule) \
                    .filter(Schedule.role == role, MachineInterface.as_boot == True):
                ips.append(machine.interfaces[0].ipv4)

        return ips
