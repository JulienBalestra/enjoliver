"""
Over the application Model, queries to the database
"""

import datetime
import os
import socket

from sqlalchemy.orm import Session

import logging
import sync
from model import ChassisPort, Chassis, MachineInterface, Machine, MachineDisk, \
    Healthz, Schedule, ScheduleRoles, LifecycleIgnition, LifecycleCoreosInstall, LifecycleRolling
from smartdb import SmartDatabaseClient as sc

logger = logging.getLogger(__name__)


class FetchDiscovery(object):
    """
    Get data created during the discovery phase
    """

    def __init__(self, session, ignition_journal):
        self.session = session
        self.ignition_journal = ignition_journal

    def _get_chassis_name(self, machine_interface):
        chassis_port = self.session.query(ChassisPort).filter(
            ChassisPort.machine_interface == machine_interface.id
        ).first()
        if chassis_port:
            chassis_name = self.session.query(Chassis).filter(
                Chassis.id == chassis_port.chassis_id
            ).first().name
            return chassis_name

        return None

    def get_all_interfaces(self):
        return [
            {
                "mac": i.mac,
                "name": i.name,
                "netmask": i.netmask,
                "ipv4": i.ipv4,
                "cidrv4": i.cidrv4,
                "as_boot": i.as_boot,
                "machine": self.session.query(Machine).filter(Machine.id == i.machine_id).first().uuid,
                "gateway": i.gateway,
                "chassis_name": self._get_chassis_name(i),
                "fqdn": i.fqdn,
            } for i in self.session.query(MachineInterface)]

    def get_ignition_journal(self, uuid: str, boot_id=None):
        lines = []

        if type(uuid) is not str and len(uuid) != 36:
            return lines
        uuid_directory = "%s/%s" % (self.ignition_journal, uuid)

        if boot_id is None and os.path.isdir(uuid_directory):
            boot_id_list = []
            for d in os.listdir(uuid_directory):
                boot_id_list.append((d, os.stat("%s/%s" % (uuid_directory, d)).st_ctime))

            boot_id_list.sort(key=lambda uplet: uplet[1])

            with open("%s/%s" % (uuid_directory, boot_id_list[0][0]), "r") as log:
                lines = log.readlines()

        elif os.path.isdir(uuid_directory):
            boot_id_file = "%s/%s" % (uuid_directory, boot_id)
            try:
                with open(boot_id_file, 'r') as log:
                    lines = log.readlines()
            except OSError:
                pass

        return lines

    def get_ignition_journal_summary(self):
        summaries = []
        try:
            ign_dir = os.listdir(self.ignition_journal)
            for uuid in ign_dir:
                summary = dict()
                summary["uuid"] = uuid
                boot_id_list = []
                uuid_directory = "%s/%s" % (self.ignition_journal, uuid)
                for d in os.listdir(uuid_directory):
                    boot_id_list.append({
                        "ctime": os.stat("%s/%s" % (uuid_directory, d)).st_ctime,
                        "boot_id": d})

                boot_id_list.sort(key=lambda d: d["ctime"])
                summary["boot_id_list"] = boot_id_list
                summaries.append(summary)

            return summaries

        except OSError:
            return summaries

    def get_all(self):
        all_data = []
        for machine in self.session.query(Machine):
            m = dict()

            m["interfaces"] = [
                {
                    "mac": k.mac,
                    "name": k.name,
                    "netmask": k.netmask,
                    "ipv4": k.ipv4,
                    "cidrv4": k.cidrv4,
                    "as_boot": k.as_boot,
                    "gateway": k.gateway,
                    "fqdn": k.fqdn,
                } for k in machine.interfaces
            ]
            interface_boot = self.session.query(MachineInterface).filter(
                MachineInterface.machine_id == machine.id and
                MachineInterface.as_boot is True).first()

            m["boot-info"] = {
                "uuid": machine.uuid,
                "mac": interface_boot.mac,
                "created-date": machine.created_date,
                "updated-date": machine.updated_date,
            }

            m["disks"] = [
                {
                    'size-bytes': k.size,
                    'path': k.path,
                } for k in machine.disks
            ]

            all_data.append(m)

        return all_data


def health_check(session: Session, ts: int, who: str):
    """
    :param session: a constructed session
    :param ts: timestamp
    :param who: the host who asked for the check
    :return:
    """
    health = session.query(Healthz).first()
    if not health:
        health = Healthz()
        session.add(health)
    health.ts = ts
    health.host = who
    session.commit()
    return True


def health_check_purge(session):
    session.query(Healthz).delete()
    session.commit()


class InjectDiscovery(object):
    """
    Store the data provides during the discovery process
    """
    def __init__(self, session: Session, ignition_journal, discovery: dict):
        """

        :param session:
        :param ignition_journal:
        :param discovery:
        """
        self.session = session
        self.ignition_journal = ignition_journal
        self.adds = 0
        self.updates = 0

        self.discovery = discovery

        step = "machine"
        try:
            self.machine, step = self._machine(), "interfaces"
            self.interfaces, step = self._machine_interfaces(), "disks"
            self.disks, step = self._machine_disk(), "chassis"

            self.chassis, step = self._chassis(), "chassis_port"
            self.chassis_port, step = self._chassis_port(), "ignition_journal"

            self._ignition_journal()
        except Exception as e:
            logger.error("raise: %s %s %s -> %s" % (step, type(e), e, self.discovery))
            raise

    def _machine(self):
        uuid = self.discovery["boot-info"]["uuid"]
        if len(uuid) != 36:
            logger.error("uuid: %s in not len(36)")
            raise TypeError("uuid: %s in not len(36)" % uuid)
        machine = self.session.query(Machine).filter(Machine.uuid == uuid).first()
        if machine:
            logger.debug("machine %s already in db" % uuid)
            machine.updated_date = datetime.datetime.utcnow()
            self.updates += 1
            return machine
        machine = Machine(uuid=uuid)
        self.session.add(machine)
        self.adds += 1
        return machine

    def _get_verifed_dns_query(self, interface: dict):
        """
        A discovery machine give a FQDN. This method will do the resolution before insert in the db
        :param interface:
        :return:
        """
        fqdn = []
        try:
            for name in interface["fqdn"]:
                try:
                    r = socket.gethostbyaddr(interface["ipv4"])[0]
                    logger.debug("succeed to make dns request for %s:%s" % (interface["ipv4"], r))
                    if name[-1] == ".":
                        name = name[:-1]

                    if name == r:
                        fqdn.append(name)
                    else:
                        logger.warning(
                            "fail to verify domain name discoveryC %s != %s socket.gethostbyaddr for %s %s" % (
                                name, r, interface["ipv4"], interface["mac"]))
                except socket.herror:
                    logger.error("Verify FAILED '%s':%s socket.herror returning None" % (name, interface["ipv4"]))

        except (KeyError, TypeError):
            logger.warning("No fqdn for %s returning None" % interface["ipv4"])

        if fqdn and len(fqdn) > 1:
            raise AttributeError("Should be only one: %s" % fqdn)
        return fqdn[0] if fqdn else None

    def _machine_interfaces(self):
        m_interfaces = self.machine.interfaces

        for interface in self.discovery["interfaces"]:
            # TODO make only one query instead of many
            if interface["mac"] and self.session.query(MachineInterface).filter(
                            MachineInterface.mac == interface["mac"]).count() == 0:
                logger.debug("mac not in db: %s adding" % interface["mac"])

                fqdn = self._get_verifed_dns_query(interface)

                m_interfaces.append(
                    MachineInterface(
                        name=interface["name"],
                        netmask=interface["netmask"],
                        mac=interface["mac"],
                        ipv4=interface["ipv4"],
                        cidrv4=interface["cidrv4"],
                        as_boot=True if interface["mac"] == self.discovery["boot-info"]["mac"] else False,
                        gateway=interface["gateway"],
                        fqdn=fqdn,
                        machine_id=self.machine.id)
                )
                self.adds += 1

        return m_interfaces

    def _machine_disk(self):
        m_disks = []

        if not self.discovery["disks"]:
            logger.error("machineID: %s haven't any disk" % self.machine.id)
            return m_disks

        for disk in self.discovery["disks"]:
            if self.session.query(MachineDisk).filter(MachineDisk.machine_id == self.machine.id).filter(
                            MachineDisk.path == disk["path"]).count() == 0:
                md = MachineDisk(
                    machine_id=self.machine.id,
                    path=disk["path"],
                    size=disk["size-bytes"]
                )
                self.session.add(md)
                m_disks.append(md)
                self.adds += 1

        return m_disks

    def _chassis(self):
        chassis_list = []
        if self.discovery["lldp"]["is_file"] is False or not self.discovery["lldp"]["data"]["interfaces"]:
            return chassis_list
        for lldp_intefaces in self.discovery["lldp"]["data"]["interfaces"]:
            chassis = self.session.query(Chassis).filter(Chassis.mac == lldp_intefaces["chassis"]["id"]).count()
            if chassis == 0:
                logger.debug(
                    "chassis %s %s not in db" % (lldp_intefaces["chassis"]["name"], lldp_intefaces["chassis"]["id"]))
                chassis = Chassis(
                    name=lldp_intefaces["chassis"]["name"],
                    mac=lldp_intefaces["chassis"]["id"]
                )
                self.session.add(chassis)
                self.adds += 1
            chassis_list.append(chassis)

        return chassis_list

    def __get_mac_by_name(self, name: str):
        for interface in self.discovery["interfaces"]:
            if interface["name"] == name:
                return interface["mac"]

    def _chassis_port(self):
        chassis_port_list = []
        if self.discovery["lldp"]["is_file"] is False or not self.discovery["lldp"]["data"]["interfaces"]:
            return chassis_port_list

        for entry in self.discovery["lldp"]["data"]["interfaces"]:
            exist = self.session.query(ChassisPort).filter(ChassisPort.mac == entry["port"]["id"]).count()
            chassis = self.session.query(Chassis).filter(Chassis.mac == entry["chassis"]["id"]).first()
            # The ChassisPort doesn't exist
            if exist == 0:
                # Get the mac address of the MachineInterface by his name inside the DiscoveryPOST
                machine_interface_mac = self.__get_mac_by_name(entry["name"])
                machine_interface = self.session.query(MachineInterface).filter(
                    MachineInterface.mac == machine_interface_mac).first()
                chassis_port = ChassisPort(
                    mac=entry["port"]["id"],
                    chassis_id=chassis.id,
                    machine_interface=machine_interface.id
                )
                self.session.add(chassis_port)
                self.adds += 1
                chassis_port_list.append(chassis_port)

        return chassis_port_list

    def _ignition_journal(self):
        boot_id = self.discovery["boot-info"]["random-id"]
        uuid = self.discovery["boot-info"]["uuid"]
        if self.discovery["ignition-journal"] is None:
            return

        if os.path.isdir("%s/%s" % (self.ignition_journal, uuid)) is False:
            os.makedirs("%s/%s" % (self.ignition_journal, uuid))

        with open("%s/%s/%s" % (self.ignition_journal, uuid, boot_id), "w") as f:
            f.write("\n".join(self.discovery["ignition-journal"]))

    def commit(self, report=True):
        try:
            if self.adds != 0 or self.updates != 0:
                try:
                    logger.debug("committing")
                    self.session.commit()

                except Exception as e:
                    logger.error("%s %s adds=%s updates=%s" % (type(e), e, self.adds, self.updates))
                    self.adds, self.updates = 0, 0
                    logger.warning("rollback the sessions")
                    self.session.rollback()
                    raise
        finally:
            if report:
                machine_nb = self.session.query(Machine).count()
                logger.debug("closing")
                return machine_nb, True if self.adds else False


class FetchSchedule(object):
    """
    Retrieve the information about schedules
    """

    def __init__(self, session: Session):
        self.session = session

    def get_schedules(self):
        r = {}
        for machine in self.session.query(Machine).join(
                Schedule).filter(MachineInterface.as_boot == True):
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
        for machine in self.session.query(Machine).join(Schedule).filter(Schedule.role == role):
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
        for machine in self.session.query(Machine).join(MachineInterface).join(Schedule).filter(
                        Schedule.role == role, MachineInterface.as_boot == True):
            ips.append(
                machine.interfaces[0].ipv4
            )
        return ips


class InjectSchedule(object):
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


class InjectLifecycle(object):
    """
    Store the data from the Lifecycle machine state
    """
    def __init__(self, session, request_raw_query):
        self.session = session
        self.adds = 0
        self.updates = 0

        self.mac = self.get_mac_from_raw_query(request_raw_query)

        self.machine = self.session.query(Machine).join(MachineInterface).filter(
            MachineInterface.mac == self.mac).first()
        if not self.machine:
            m = "InjectLifecycle mac: '%s' unknown in db" % self.mac
            logger.error(m)
            raise AttributeError(m)
        logger.debug("InjectLifecycle mac: %s" % self.mac)

    @staticmethod
    def get_mac_from_raw_query(request_raw_query: str):
        mac = ""
        raw_query_list = request_raw_query.split("&")
        for param in raw_query_list:
            if "mac=" in param:
                mac = param.replace("mac=", "")
        if not mac:
            raise AttributeError("%s is not parsable" % request_raw_query)
        return mac.replace("-", ":")

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


class FetchLifecycle(object):
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


class FetchView(object):
    """
    Get the data for the User Interface View
    """
    def __init__(self, session: Session):
        self.session = session

    def get_machines(self):
        data = {
            "gridColumns": [
                "MAC",
                "CIDR",
                "FQDN",
                "DiskProfile",
                "Roles",
                "Installation",
                "UpdateStrategy",
                "UpToDate",
                "LastReport",
                "LastChange",
            ],
            "gridData": []
        }
        for machine in self.session.query(Machine).outerjoin(
                MachineInterface).outerjoin(LifecycleCoreosInstall).outerjoin(LifecycleIgnition).outerjoin(
            Schedule).outerjoin(MachineDisk).filter(MachineInterface.as_boot == True):

            coreos_install, ignition_updated_date, ignition_last_change = None, None, None
            ignition_up_to_date, lifecycle_rolling = None, None

            if machine.lifecycle_coreos_install:
                coreos_install = "Success" if machine.lifecycle_coreos_install[
                                                  0].success is True else "Failed"

            if machine.lifecycle_ignition:
                ignition_updated_date = machine.lifecycle_ignition[0].updated_date
                ignition_up_to_date = machine.lifecycle_ignition[0].up_to_date
                ignition_last_change = machine.lifecycle_ignition[0].last_change_date

            if machine.lifecycle_rolling:
                lifecycle_rolling = machine.lifecycle_rolling[0].strategy if machine.lifecycle_rolling[
                    0].enable else "Disable"

            disks = []
            if machine.disks:
                for disk in machine.disks:
                    disks.append({
                        "path": disk.path,
                        "size-bytes": disk.size
                    })
            row = {
                "Roles": ",".join([r.role for r in machine.schedules]),
                "FQDN": machine.interfaces[0].fqdn,
                "CIDR": machine.interfaces[0].cidrv4,
                "MAC": machine.interfaces[0].mac,
                "Installation": coreos_install,
                "LastReport": ignition_updated_date,
                "LastChange": ignition_last_change,
                "UpToDate": ignition_up_to_date,
                "UpdateStrategy": lifecycle_rolling,
                "DiskProfile": sync.ConfigSyncSchedules.compute_disks_size(disks)
            }

            data["gridData"].append(row)
        return data


class BackupExport(object):
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
        for schedule_type in [ScheduleRoles.kubernetes_control_plane, ScheduleRoles.kubernetes_node]:
            for schedule in self.session.query(Schedule).filter(Schedule.role == schedule_type):
                for machine in self.session.query(Machine).filter(Machine.id == schedule.machine_id):
                    discovery_data = self._construct_discovery(machine)
                    schedule_data = self._construct_schedule(discovery_data["boot-info"]["mac"], schedule_type)
                    self.playbook.append({"data": discovery_data, "route": "/discovery"})
                    self.playbook.append({"data": schedule_data, "route": "/scheduler"})

        return self.playbook
