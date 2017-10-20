"""
Over the application Model, queries to the database
"""

import datetime
import logging

from sqlalchemy.orm import Session, joinedload

import tools
from model import MachineInterface, Machine, MachineDisk, \
    Schedule, ScheduleRoles, LifecycleIgnition, LifecycleCoreosInstall, LifecycleRolling
from smartdb import SmartDatabaseClient as sc

logger = logging.getLogger(__name__)


class InjectSchedule:
    """
    Store the information of a schedule
    """

    def __init__(self, session, data):
        self.session = session
        self.adds = 0
        self.updates = 0

        self.data = data
        self.mac = self.data["selector"]["mac"]

        self.interface = self.session.query(MachineInterface).filter(MachineInterface.mac == self.mac).first()
        if not self.interface:
            m = "mac: '%s' unknown in db" % self.mac
            logger.error(m)
            raise AttributeError(m)
        logger.info("InjectSchedule mac: %s" % self.mac)

    def apply_roles(self):
        for role in self.data["roles"]:
            r = self.session.query(Schedule).filter(
                Schedule.machine_id == self.interface.machine_id).filter(Schedule.role == role).first()
            if r:
                logger.info("mac %s already scheduled as %s" % (self.mac, role))
                continue

            new = Schedule(
                machine_id=self.interface.machine_id,
                role=role
            )
            self.session.add(new)
            self.adds += 1
            logger.info("mac %s scheduling as %s" % (self.mac, role))

        return

    def commit(self, report=True):
        try:
            if self.adds != 0 or self.updates != 0:
                try:
                    logger.debug("commiting")
                    self.session.commit()

                except Exception as e:
                    logger.error("%s %s adds=%s updates=%s" % (type(e), e, self.adds, self.updates))
                    self.adds, self.updates = 0, 0
                    logger.warning("rollback the sessions")
                    self.session.rollback()
                    raise
        finally:
            if report:
                roles_rapport = {}
                for r in ScheduleRoles.roles:
                    roles_rapport[r] = self.session.query(Schedule).filter(Schedule.role == r).count()
                logger.debug("closing")
                return roles_rapport, True if self.adds else False


class InjectLifecycle:
    """
    Store the data from the Lifecycle machine state
    """

    def __init__(self, session, request_raw_query):
        self.session = session
        self.adds = 0
        self.updates = 0

        self.mac = tools.get_mac_from_raw_query(request_raw_query)

        self.machine = self.session.query(Machine).join(MachineInterface).filter(
            MachineInterface.mac == self.mac).first()
        if not self.machine:
            m = "InjectLifecycle mac: '%s' unknown in db" % self.mac
            logger.error(m)
            raise AttributeError(m)
        logger.debug("InjectLifecycle mac: %s" % self.mac)

    def refresh_lifecycle_ignition(self, up_to_date: bool):
        lifecycle = self.session.query(LifecycleIgnition).filter(
            LifecycleIgnition.machine_id == self.machine.id).first()
        if not lifecycle:
            lifecycle = LifecycleIgnition(
                machine_id=self.machine.id,
                up_to_date=up_to_date
            )
            self.session.add(lifecycle)
        else:
            now = datetime.datetime.utcnow()
            if lifecycle.up_to_date != up_to_date:
                lifecycle.last_change_date = now
            lifecycle.up_to_date = up_to_date
            lifecycle.updated_date = now

        self.session.commit()

    def refresh_lifecycle_coreos_install(self, success: bool):
        lifecycle = self.session.query(LifecycleCoreosInstall).filter(
            LifecycleCoreosInstall.machine_id == self.machine.id).first()
        if not lifecycle:
            lifecycle = LifecycleCoreosInstall(
                machine_id=self.machine.id,
                success=success
            )
            self.session.add(lifecycle)
        else:
            lifecycle.up_to_date = success
            lifecycle.updated_date = datetime.datetime.utcnow()

        self.session.commit()

    def apply_lifecycle_rolling(self, enable: bool, strategy="kexec"):
        lifecycle = self.session.query(LifecycleRolling).filter(
            LifecycleRolling.machine_id == self.machine.id).first()
        if not lifecycle:
            lifecycle = LifecycleRolling(
                machine_id=self.machine.id,
                enable=enable,
                strategy=strategy,
            )
            self.session.add(lifecycle)
        else:
            lifecycle.enable = enable
            lifecycle.strategy = strategy
            lifecycle.updated_date = datetime.datetime.utcnow()

        self.session.commit()


class FetchLifecycle:
    """
    Get the data of the Lifecycle state
    """

    def __init__(self, session: Session):
        self.session = session

    def get_ignition_uptodate_status(self, mac: str):
        for row in self.session.execute("""SELECT li.up_to_date FROM "machine-interface" AS mi
          JOIN machine AS m ON m.id = mi.machine_id
          JOIN "lifecycle-ignition" AS li ON li.machine_id = mi.machine_id
          WHERE mi.mac = :mac""", {"mac": mac}):
            return row["up_to_date"]

        return None

    def get_all_updated_status(self):
        status = []
        for machine in self.session.query(Machine).join(LifecycleIgnition).join(
                MachineInterface).filter(MachineInterface.as_boot == True):
            status.append({
                "up-to-date": machine.lifecycle_ignition[0].up_to_date,
                "fqdn": machine.interfaces[0].fqdn,
                "mac": machine.interfaces[0].mac,
                "cidrv4": machine.interfaces[0].cidrv4,
                "created_date": machine.created_date,
                "updated_date": machine.updated_date,
                "last_change_date": machine.lifecycle_ignition[0].last_change_date,
            })
        return status

    def get_coreos_install_status(self, mac: str):
        for row in self.session.execute("""SELECT lci.success FROM "machine-interface" AS mi
          JOIN machine AS m ON m.id = mi.machine_id
          JOIN "lifecycle-coreos-install" AS lci ON lci.machine_id = mi.machine_id
          WHERE mi.mac = :mac""", {"mac": mac}):
            return bool(row["success"])

        return None

    def get_all_coreos_install_status(self):
        life_status_list = []
        for machine in self.session.query(Machine).join(LifecycleCoreosInstall).join(MachineInterface).filter(
                        MachineInterface.as_boot == True):
            life_status_list.append({
                "mac": machine.interfaces[0].mac,
                "fqdn": machine.interfaces[0].fqdn,
                "cidrv4": machine.interfaces[0].cidrv4,
                "success": machine.lifecycle_coreos_install[0].success,
                "created_date": machine.lifecycle_coreos_install[0].created_date,
                "updated_date": machine.lifecycle_coreos_install[0].updated_date
            })
        return life_status_list

    def get_rolling_status(self, mac: str):
        for m in self.session.query(Machine) \
                .join(MachineInterface) \
                .filter(MachineInterface.mac == mac) \
                .join(LifecycleRolling):
            try:
                rolling = m.lifecycle_rolling[0]
                return rolling.enable, rolling.strategy
            except IndexError:
                pass

        logger.debug("mac: %s return None" % mac)
        return None, None

    def get_all_rolling_status(self):
        life_roll_list = []
        for machine in self.session.query(Machine) \
                .join(LifecycleRolling) \
                .join(MachineInterface) \
                .options(joinedload("interfaces")) \
                .options(joinedload("lifecycle_rolling")) \
                .filter(MachineInterface.as_boot == True):
            try:
                life_roll_list.append({
                    "mac": machine.interfaces[0].mac,
                    "fqdn": machine.interfaces[0].fqdn,
                    "cidrv4": machine.interfaces[0].cidrv4,
                    "enable": bool(machine.lifecycle_rolling[0].enable),
                    "created_date": machine.lifecycle_rolling[0].created_date,
                    "updated_date": machine.lifecycle_rolling[0].updated_date
                })
            except IndexError:
                pass
        return life_roll_list


class BackupExport:
    def __init__(self, session: Session):
        self.session = session
        self.playbook = []

    @staticmethod
    def _construct_discovery(machine: Machine):
        interfaces = list()
        mac_boot = ""
        for interface in machine.interfaces:
            if interface.as_boot is True:
                mac_boot = interface.mac
            interfaces.append({
                'mac': interface.mac,
                'netmask': interface.netmask,
                'ipv4': interface.ipv4,
                'cidrv4': interface.ipv4,
                'name': interface.name,
                "gateway": interface.gateway,
                "fqdn": [interface.fqdn]
            })
        if mac_boot == "":
            raise LookupError("fail to retrieve mac boot in %s" % interfaces)

        return {
            "boot-info": {
                "uuid": machine.uuid,
                "mac": mac_boot,
                "random-id": "",
            },

            "interfaces": interfaces,
            "disks": [{
                'size-bytes': k.size,
                'path': k.path
            } for k in machine.disks],

            # TODO LLDP
            "lldp": {
                'data': {'interfaces': None},
                'is_file': False
            },

            "ignition-journal": None
        }

    @staticmethod
    def _construct_schedule(mac: str, schedule_type: str):
        """
        Construct the schedule as the scheduler does
        :param mac:
        :param schedule_type:
        :return: dict
        """
        # TODO maybe decide to drop etcd-member because it's tricky to deal with two roles
        # etcd-member + kubernetes-control-plane: in fact it's only one
        if schedule_type == ScheduleRoles.kubernetes_control_plane:
            roles = [ScheduleRoles.kubernetes_control_plane, ScheduleRoles.etcd_member]
        else:
            roles = [ScheduleRoles.kubernetes_node]
        return {
            u"roles": roles,
            u'selector': {
                u"mac": mac
            }
        }

    def get_playbook(self):
        """
        Get and reproduce the data sent inside the db from an API level
        :return:
        """
        # TODO use the ORM loading
        for schedule_type in [ScheduleRoles.kubernetes_control_plane, ScheduleRoles.kubernetes_node]:
            for schedule in self.session.query(Schedule).filter(Schedule.role == schedule_type):
                for machine in self.session.query(Machine).filter(Machine.id == schedule.machine_id):
                    discovery_data = self._construct_discovery(machine)
                    schedule_data = self._construct_schedule(discovery_data["boot-info"]["mac"], schedule_type)
                    self.playbook.append({"data": discovery_data, "route": "/discovery"})
                    self.playbook.append({"data": schedule_data, "route": "/scheduler"})

        return self.playbook
