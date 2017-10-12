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


class FetchSchedule:
    """
    Retrieve the information about schedules
    """

    def __init__(self, session: Session):
        self.session = session

    def get_schedules(self):
        r = {}
        for machine in self.session.query(Machine) \
                .options(joinedload("interfaces")) \
                .options(joinedload("schedules")) \
                .join(Schedule) \
                .filter(MachineInterface.as_boot == True):
            r[machine.interfaces[0].mac] = [k.role for k in machine.schedules]

        return r

    def get_roles_by_mac_selector(self, mac: str):
        r = []
        for s in self.session.query(Schedule).join(Machine).join(MachineInterface).filter(MachineInterface.mac == mac):
            r.append(s.role)
        return r

    def get_available_machines(self):
        available_machines = []

        for row in self.session.execute("""SELECT mi.id, mi.mac, mi.ipv4, mi.cidrv4, mi.gateway, mi.as_boot, mi.name, mi.netmask, mi.fqdn, mi.machine_id FROM machine AS m
            LEFT JOIN schedule AS s ON m.id = s.machine_id
            INNER JOIN  "machine-interface" AS mi ON mi.machine_id = m.id AND mi.as_boot = :as_boot
            WHERE s.role IS NULL""", {"as_boot": sc.get_bool_by_session(self.session, True)}):
            available_machines.append({
                "mac": row["mac"],
                "ipv4": row["ipv4"],
                "cidrv4": row["cidrv4"],
                "gateway": row["gateway"],
                "as_boot": row["as_boot"],
                "name": row["name"],
                "netmask": row["netmask"],
                "created_date": self.session.query(Machine).filter(
                    Machine.id == row["machine_id"]).first().created_date,
                "fqdn": row["fqdn"],
                "disks": [{"path": k.path, "size-bytes": k.size}
                          for k in self.session.query(MachineDisk).filter(MachineDisk.id == row["machine_id"])],
            })
        return available_machines

    def get_machines_by_role(self, role: str):
        machines = []
        for machine in self.session.query(Machine) \
                .options(joinedload("interfaces")) \
                .options(joinedload("disks")) \
                .join(Schedule) \
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

    def get_machines_by_roles(self, *args):
        machines = []
        if len(args) > 1:
            union = ["""INNER JOIN (SELECT m.id FROM machine AS m
              INNER JOIN schedule AS s ON s.machine_id = m.id
              WHERE s.role = '%s') AS b ON a.machine_id = b.id""" % k for k in args[1:]]

            query = """SELECT result.machine_id, mi.mac, mi.ipv4, mi.cidrv4, mi.gateway, mi.as_boot, mi.name, mi.netmask, mi.fqdn FROM (
            (SELECT m.id as machine_id FROM machine AS m
            INNER JOIN schedule AS s ON s.machine_id = m.id
            WHERE s.role = '%s') AS a %s) AS result
            INNER JOIN "machine-interface" AS mi ON mi.machine_id = result.machine_id
            WHERE mi.as_boot = %s""" % (args[0], " ".join(union),
                                        sc.get_bool_by_session(self.session, True))

            for row in self.session.execute(query):
                machines.append({
                    "mac": row[sc.get_select_by_session(self.session, "mi", "mac")],
                    "ipv4": row[sc.get_select_by_session(self.session, "mi", "ipv4")],
                    "cidrv4": row[sc.get_select_by_session(self.session, "mi", "cidrv4")],
                    "gateway": row[sc.get_select_by_session(self.session, "mi", "gateway")],
                    "as_boot": row[sc.get_select_by_session(self.session, "mi", "as_boot")],
                    "name": row[sc.get_select_by_session(self.session, "mi", "name")],
                    "netmask": row[sc.get_select_by_session(self.session, "mi", "netmask")],
                    "roles": list(args),
                    "created_date": self.session.query(Machine).filter(
                        Machine.id == row[
                            sc.get_select_by_session(self.session, "result", "machine_id")]).first().created_date,
                    "fqdn": row[sc.get_select_by_session(self.session, "mi", "fqdn")],
                    "disks": [{"path": k.path, "size-bytes": k.size}
                              for k in
                              self.session.query(MachineDisk).filter(
                                  MachineDisk.id == row[
                                      sc.get_select_by_session(self.session, "result", "machine_id")])],
                })
            return machines

        return self.get_machines_by_role(*args)

    def get_role_ip_list(self, role: str):
        ips = []
        for machine in self.session.query(Machine) \
                .options(joinedload("interfaces")) \
                .join(MachineInterface) \
                .join(Schedule) \
                .filter(Schedule.role == role, MachineInterface.as_boot == True):
            ips.append(
                machine.interfaces[0].ipv4
            )
        return ips


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
        for row in self.session.execute("""SELECT lr.enable, lr.strategy FROM "machine-interface" AS mi
          JOIN machine AS m ON m.id = mi.machine_id
          JOIN "lifecycle-rolling" AS lr ON lr.machine_id = mi.machine_id
          WHERE mi.mac = :mac""", {"mac": mac}):
            return bool(row["enable"]), row["strategy"]

        logger.debug("mac: %s return None" % mac)
        return None, None

    def get_all_rolling_status(self):
        life_roll_list = []
        for machine in self.session.query(Machine).join(LifecycleRolling).join(MachineInterface).filter(
                        MachineInterface.as_boot == True):
            life_roll_list.append(
                {
                    "mac": machine.interfaces[0].mac,
                    "fqdn": machine.interfaces[0].fqdn,
                    "cidrv4": machine.interfaces[0].cidrv4,
                    "enable": bool(machine.lifecycle_rolling[0].enable),
                    "created_date": machine.lifecycle_rolling[0].created_date,
                    "updated_date": machine.lifecycle_rolling[0].updated_date
                }
            )
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
