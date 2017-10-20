import datetime
import logging

from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session

import smartdb
import tools
from model import MachineInterface, Machine, MachineDisk, Chassis, ChassisPort
from smartdb import cockroach_transaction

logger = logging.getLogger(__file__)


class DiscoveryRepository:
    __name__ = "DiscoveryRepository"

    def __init__(self, smart: smartdb.SmartDatabaseClient):
        self.smart = smart

    @staticmethod
    def _lint_discovery_data(discovery_data: dict):
        # ignore ignition-journal: NotImplemented
        missing_keys = {"boot-info", "disks", "lldp", "interfaces"} - set(discovery_data.keys())
        if missing_keys:
            err_msg = "missing keys in discovery data: '%s'", ",".join(missing_keys)
            logger.error(err_msg)
            raise TypeError(err_msg)

        if discovery_data["disks"] is None:
            discovery_data["disks"] = list()
        return discovery_data

    @staticmethod
    def _delete_all_attached(session: Session, machine: Machine):
        """
        Delete all resources attached to a machine
        As we don't need performance we can avoid heuristics by dropping and re-creating theses needed resources
        The discovery data is the reference of the reality
        :param session:
        :param machine:
        :return:
        """
        session.query(MachineDisk) \
            .filter(MachineDisk.machine_id == machine.id) \
            .delete()

        all_mi = session.query(MachineInterface) \
            .filter(MachineInterface.machine_id == machine.id)
        for i in all_mi:
            session.query(ChassisPort) \
                .filter(ChassisPort.machine_interface == i.id) \
                .delete()
            session.delete(i)

        session.flush()

    @staticmethod
    def _insert_network(session: Session, machine: Machine, discovery_data: dict):
        machine_interfaces = dict()
        for i in discovery_data["interfaces"]:
            if i["mac"]:
                machine_interface = MachineInterface(
                    mac=i["mac"],
                    name=i["name"],
                    netmask=i["netmask"],
                    ipv4=i["ipv4"],
                    cidrv4=i["cidrv4"],
                    as_boot=i["mac"] == discovery_data["boot-info"]["mac"],
                    gateway=i["gateway"],
                    fqdn=tools.get_verified_dns_query(i),
                    machine_id=machine.id
                )
                # track machine interfaces to get them after during the LLDP section
                machine_interfaces[machine_interface.name] = machine_interface
                session.add(machine_interface)

        session.flush()

        if discovery_data["lldp"]["is_file"] and discovery_data["lldp"]["data"]["interfaces"]:
            for lldp_interface in discovery_data["lldp"]["data"]["interfaces"]:
                chassis = session.query(Chassis) \
                    .filter(Chassis.name == lldp_interface["chassis"]["name"] and
                            Chassis.name == lldp_interface["chassis"]["id"]) \
                    .first()
                if not chassis:
                    chassis = Chassis(
                        name=lldp_interface["chassis"]["name"],
                        mac=lldp_interface["chassis"]["id"],
                    )
                session.add(chassis)
                session.flush()
                machine_interface_id = machine_interfaces[lldp_interface["name"]].id
                session.add(
                    ChassisPort(
                        # TODO on some vendor it's not a MAC but a string like Ethernet1/22
                        mac=lldp_interface["port"]["id"],
                        machine_interface=machine_interface_id,
                        chassis_id=chassis.id
                    )
                )

    def upsert(self, discovery_data: dict):
        caller = "%s.%s" % (self.__name__, self.upsert.__name__)
        discovery_data = self._lint_discovery_data(discovery_data)
        now = datetime.datetime.utcnow()

        @cockroach_transaction
        def callback(caller=caller):
            new = True
            with self.smart.new_session() as session:

                machine = session.query(Machine) \
                    .filter(Machine.uuid == discovery_data["boot-info"]["uuid"]) \
                    .first()

                if machine:
                    new = False
                    machine.updated_date = now
                    self._delete_all_attached(session, machine)
                else:
                    machine = Machine(uuid=discovery_data["boot-info"]["uuid"], created_date=now, updated_date=now)
                    session.add(machine)
                    session.flush()

                for d in discovery_data["disks"]:
                    session.add(MachineDisk(path=d["path"], size=d["size-bytes"], machine_id=machine.id))

                self._insert_network(session, machine, discovery_data)
                session.commit()
            return new

        return callback(caller)

    def fetch_all_discovery(self):
        """
        Get discovery data of interfaces, disks and the boot-info
        :return:
        """
        machines = []
        with self.smart.new_session() as session:
            for m in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .join(MachineInterface):

                boot_interface = None
                interfaces = []
                for i in m.interfaces:
                    if i.as_boot:
                        boot_interface = i
                    interfaces.append({
                        "as_boot": i.as_boot,
                        "cidrv4": i.cidrv4,
                        "fqdn": i.fqdn,
                        "gateway": i.gateway,
                        "ipv4": i.ipv4,
                        "mac": i.mac,
                        "name": i.name,
                        "netmask": i.netmask
                    })

                machines.append({
                    "boot-info": {
                        "uuid": m.uuid,
                        "created-date": m.created_date,
                        "updated-date": m.updated_date,
                        "mac": boot_interface.mac
                    },
                    "interfaces": interfaces,
                    "disks": [{"size-bytes": d.size, "path": d.path} for d in m.disks]
                })
            return machines
