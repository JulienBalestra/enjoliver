from sqlalchemy.orm import joinedload

import smartdb
from model import Machine, Schedule, MachineInterface


class ScheduleRepository:
    def __init__(self, smart: smartdb.SmartDatabaseClient):
        self.smart = smart

    def get_all_schedules(self):
        result = dict()
        with self.smart.new_session() as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("schedules")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True):
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
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .filter(MachineInterface.as_boot == True) \
                    .filter(Machine.schedules == None):
                available_machines.append(
                    {
                        "mac": m.interfaces[0].mac,
                        "ipv4": m.interfaces[0].ipv4,
                        "cidrv4": m.interfaces[0].cidrv4,
                        "as_boot": m.interfaces[0].as_boot,
                        "name": m.interfaces[0].name,
                        "fqdn": m.interfaces[0].fqdn,
                        "netmask": m.interfaces[0].netmask,
                        "created_date": m.created_date,
                        "disks": [{"path": k.path, "size-bytes": k.size} for k in m.disks],

                    }
                )

        return available_machines

    def get_machines_by_role(self, role: str):
        machines = []
        with self.smart.new_session() as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True) \
                    .filter(Schedule.role == role):
                machines.append({
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
                })

        return machines
