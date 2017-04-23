"""
Over the application Model, queries to the database
"""

import datetime
import os
import socket
from sqlalchemy import func
from sqlalchemy.orm import subqueryload

import logger
from model import ChassisPort, Chassis, MachineInterface, Machine, \
    Healthz, Schedule, ScheduleRoles, LifecycleIgnition, LifecycleCoreosInstall, LifecycleRolling

LOGGER = logger.get_logger(__file__)


class FetchDiscovery(object):
    """
    Get data created during the discovery phase
    """

    def __init__(self, session, ignition_journal):
        self.session = session
        self.ignition_journal = ignition_journal

    def _get_chassis_name(self, machine_interface):
        chassis_port = self.session.query(ChassisPort).filter(
            ChassisPort.machine_interface_id == machine_interface.id
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

    def get_ignition_journal(self, uuid, boot_id=None):
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
        for machine in self.session.query(Machine).order_by(Machine.updated_date.desc()).options(
                subqueryload(Machine.interfaces)):
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
                } for k in machine.interfaces]
            interface_boot = self.session.query(MachineInterface).filter(
                MachineInterface.machine_id == machine.id and
                MachineInterface.as_boot is True).first()

            m["boot-info"] = {
                "uuid": machine.uuid,
                "mac": interface_boot.mac,
                "created-date": machine.created_date,
                "updated-date": machine.updated_date,
            }

            all_data.append(m)

        return all_data


def health_check(session, ts, who):
    """
    :param session: a constructed session
    :param ts: timestamp
    :param who: the host who asked for the check
    :return:
    """
    health = Healthz()
    health.ts = ts
    health.host = who
    session.add(health)
    session.commit()
    return True


def health_check_purge(session, ts):
    session.query(Healthz).filter(Healthz.ts < ts).delete()
    session.commit()


class InjectDiscovery(object):
    """
    Store the data provides during the discovery process
    """
    log = logger.get_logger(__file__)

    def __init__(self, session, ignition_journal, discovery):
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
            self.interfaces, step = self._machine_interfaces(), "chassis"

            self.chassis, step = self._chassis(), "chassis_port"
            self.chassis_port, step = self._chassis_port(), "ignition_journal"

            self._ignition_journal()
        except Exception as e:
            self.log.error("raise: %s %s %s -> %s" % (step, type(e), e, self.discovery))
            raise

    def _machine(self):
        uuid = self.discovery["boot-info"]["uuid"]
        if len(uuid) != 36:
            self.log.error("uuid: %s in not len(36)")
            raise TypeError("uuid: %s in not len(36)" % uuid)
        machine = self.session.query(Machine).filter(Machine.uuid == uuid).first()
        if machine:
            self.log.debug("machine %s already in db" % uuid)
            machine.updated_date = datetime.datetime.utcnow()
            self.updates += 1
            return machine
        machine = Machine(uuid=uuid)
        self.session.add(machine)
        self.adds += 1
        return machine

    def _get_verifed_dns_query(self, interface):
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
                    self.log.debug("succeed to make dns request for %s:%s" % (interface["ipv4"], r))
                    if name[-1] == ".":
                        name = name[:-1]

                    if name == r:
                        fqdn.append(name)
                    else:
                        self.log.warning(
                            "fail to verify domain name discoveryC %s != %s socket.gethostbyaddr for %s %s" % (
                                name, r, interface["ipv4"], interface["mac"]))
                except socket.herror:
                    self.log.error("Verify FAILED '%s':%s socket.herror returning None" % (name, interface["ipv4"]))

        except (KeyError, TypeError):
            self.log.warning("No fqdn for %s returning None" % interface["ipv4"])

        if fqdn and len(fqdn) > 1:
            raise AttributeError("Should be only one: %s" % fqdn)
        return fqdn[0] if fqdn else None

    def _machine_interfaces(self):
        m_interfaces = self.machine.interfaces

        for interface in self.discovery["interfaces"]:
            # TODO make only one query instead of many
            if interface["mac"] and self.session.query(MachineInterface).filter(
                            MachineInterface.mac == interface["mac"]).count() == 0:
                self.log.debug("mac not in db: %s adding" % interface["mac"])

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

    def _chassis(self):
        chassis_list = []
        if self.discovery["lldp"]["is_file"] is False or not self.discovery["lldp"]["data"]["interfaces"]:
            return chassis_list
        for lldp_intefaces in self.discovery["lldp"]["data"]["interfaces"]:
            chassis = self.session.query(Chassis).filter(Chassis.mac == lldp_intefaces["chassis"]["id"]).count()
            if chassis == 0:
                self.log.debug(
                    "chassis %s %s not in db" % (lldp_intefaces["chassis"]["name"], lldp_intefaces["chassis"]["id"]))
                chassis = Chassis(
                    name=lldp_intefaces["chassis"]["name"],
                    mac=lldp_intefaces["chassis"]["id"]
                )
                self.session.add(chassis)
                self.adds += 1
            chassis_list.append(chassis)

        return chassis_list

    def __get_mac_by_name(self, name):
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
                    machine_interface_id=machine_interface.id
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
                    self.log.debug("commiting")
                    self.session.commit()
                    # self.session.commit()

                except Exception as e:
                    self.log.error("%s %s adds=%s updates=%s" % (type(e), e, self.adds, self.updates))
                    self.adds, self.updates = 0, 0
                    self.log.warning("rollback the sessions")
                    self.session.rollback()
                    raise
        finally:
            if report:
                machine_nb = self.session.query(Machine).count()
                self.log.debug("closing")
                return machine_nb, True if self.adds else False


class FetchSchedule(object):
    """
    Retrieve the information about schedules
    """

    def __init__(self, session):
        self.session = session

    def get_schedules(self):
        r = {}
        for interface in self.session.query(Schedule, MachineInterface).join(
                MachineInterface):
            try:
                r[interface[1].mac] += [interface[0].role]
            except KeyError:
                r[interface[1].mac] = [interface[0].role]

        return r

    def get_roles_by_mac_selector(self, mac):
        s = self.session.query(Schedule).join(MachineInterface).filter(MachineInterface.mac == mac).all()
        r = [k.role for k in s]
        return r

    def get_available_machines(self):
        available_machines = []
        for i in self.session.query(MachineInterface).outerjoin(
                Schedule, MachineInterface.id == Schedule.machine_interface).filter(
                    MachineInterface.as_boot == True).filter(Schedule.machine_interface == None):
            available_machines.append(
                {
                    "mac": i.mac,
                    "ipv4": i.ipv4,
                    "cidrv4": i.cidrv4,
                    "gateway": i.gateway,
                    "as_boot": i.as_boot,
                    "name": i.name,
                    "netmask": i.netmask,
                    "roles": [k.role for k in i.schedule],
                    "fqdn": i.fqdn
                }
            )
        return available_machines

    def get_role(self, role):
        all_roles = []
        for i in self.session.query(Schedule).filter(Schedule.role == role):
            all_roles.append({
                "mac": i.interface.mac,
                "ipv4": i.interface.ipv4,
                "cidrv4": i.interface.cidrv4,
                "gateway": i.interface.gateway,
                "as_boot": i.interface.as_boot,
                "name": i.interface.name,
                "netmask": i.interface.netmask,
                "role": i.role,
                "created_date": i.created_date,
                "fqdn": i.interface.fqdn
            })

        return all_roles

    def get_roles(self, *args):
        roles = []
        for i in self.session.query(MachineInterface).join(Schedule).filter(
                Schedule.role.in_(args)
        ).group_by(MachineInterface).having(func.count(MachineInterface.id) == len(args)):
            roles.append(
                {
                    "mac": i.mac,
                    "ipv4": i.ipv4,
                    "cidrv4": i.cidrv4,
                    "gateway": i.gateway,
                    "as_boot": i.as_boot,
                    "name": i.name,
                    "netmask": i.netmask,
                    "fqdn": i.fqdn,
                    "roles": [k.role for k in i.schedule]
                }
            )
        return roles

    def get_role_ip_list(self, role):
        query = self.session.query(Schedule).filter(Schedule.role == role)

        return [k.interface.ipv4 for k in query]


class InjectSchedule(object):
    """
    Store the information of a schedule
    """
    log = logger.get_logger(__file__)

    def __init__(self, session, data):
        self.session = session
        self.adds = 0
        self.updates = 0

        self.data = data
        self.mac = self.data["selector"]["mac"]

        self.interface = self.session.query(MachineInterface).filter(MachineInterface.mac == self.mac).first()
        if not self.interface:
            m = "mac: '%s' unknown in db" % self.mac
            self.log.error(m)
            raise AttributeError(m)
        self.log.info("InjectSchedule mac: %s" % self.mac)

    def apply_roles(self):
        for role in self.data["roles"]:
            r = self.session.query(Schedule).filter(
                Schedule.machine_interface == self.interface.id).filter(Schedule.role == role).first()
            if r:
                self.log.info("mac %s already scheduled as %s" % (self.mac, role))
                continue

            new = Schedule(
                machine_interface=self.interface.id,
                role=role
            )
            self.session.add(new)
            self.adds += 1
            self.log.info("mac %s scheduling as %s" % (self.mac, role))

        return

    def commit(self, report=True):
        try:
            if self.adds != 0 or self.updates != 0:
                try:
                    self.log.debug("commiting")
                    self.session.commit()

                except Exception as e:
                    self.log.error("%s %s adds=%s updates=%s" % (type(e), e, self.adds, self.updates))
                    self.adds, self.updates = 0, 0
                    self.log.warning("rollback the sessions")
                    self.session.rollback()
                    raise
        finally:
            if report:
                roles_rapport = {}
                for r in ScheduleRoles.roles:
                    roles_rapport[r] = self.session.query(Schedule).filter(Schedule.role == r).count()
                self.log.debug("closing")
                return roles_rapport, True if self.adds else False


class InjectLifecycle(object):
    """
    Store the data from the Lifecycle machine state
    """
    log = logger.get_logger(__file__)

    def __init__(self, session, request_raw_query):
        self.session = session
        self.adds = 0
        self.updates = 0

        self.mac = self.get_mac_from_raw_query(request_raw_query)

        self.interface = self.session.query(MachineInterface).filter(MachineInterface.mac == self.mac).first()
        if not self.interface:
            m = "InjectLifecycle mac: '%s' unknown in db" % self.mac
            self.log.error(m)
            raise AttributeError(m)
        self.log.debug("InjectLifecycle mac: %s" % self.mac)

    @staticmethod
    def get_mac_from_raw_query(request_raw_query):
        mac = ""
        raw_query_list = request_raw_query.split("&")
        for param in raw_query_list:
            if "mac=" in param:
                mac = param.replace("mac=", "")
        if not mac:
            raise AttributeError("%s is not parsable" % request_raw_query)
        return mac.replace("-", ":")

    def refresh_lifecycle_ignition(self, up_to_date):
        lifecycle = self.session.query(LifecycleIgnition).filter(
            LifecycleIgnition.machine_interface == self.interface.id).first()
        if not lifecycle:
            lifecycle = LifecycleIgnition(
                machine_interface=self.interface.id,
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

    def refresh_lifecycle_coreos_install(self, success):
        lifecycle = self.session.query(LifecycleCoreosInstall).filter(
            LifecycleCoreosInstall.machine_interface == self.interface.id).first()
        if not lifecycle:
            lifecycle = LifecycleCoreosInstall(
                machine_interface=self.interface.id,
                success=success
            )
            self.session.add(lifecycle)
        else:
            lifecycle.up_to_date = success
            lifecycle.updated_date = datetime.datetime.utcnow()

        self.session.commit()

    def apply_lifecycle_rolling(self, enable, strategy="kexec"):
        lifecycle = self.session.query(LifecycleRolling).filter(
            LifecycleRolling.machine_interface == self.interface.id).first()
        if not lifecycle:
            lifecycle = LifecycleRolling(
                machine_interface=self.interface.id,
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
    log = logger.get_logger(__file__)

    def __init__(self, session):
        self.session = session

    def get_ignition_uptodate_status(self, mac):
        interface = self.session.query(MachineInterface).filter(MachineInterface.mac == mac).first()
        if interface:
            lifecycle = self.session.query(LifecycleIgnition).filter(
                LifecycleIgnition.machine_interface == interface.id).first()
            return lifecycle.up_to_date if lifecycle else None
        return None

    def get_all_updated_status(self):
        l = []
        for s in self.session.query(LifecycleIgnition):
            l.append(
                {
                    "up-to-date": s.up_to_date,
                    "fqdn": s.interface.fqdn,
                    "mac": s.interface.mac,
                    "cidrv4": s.interface.cidrv4,
                    "created_date": s.created_date,
                    "updated_date": s.updated_date,
                    "last_change_date": s.last_change_date,
                }
            )
        return l

    def get_coreos_install_status(self, mac):
        interface = self.session.query(MachineInterface).filter(MachineInterface.mac == mac).first()
        if interface:
            lifecycle = self.session.query(LifecycleCoreosInstall).filter(
                LifecycleCoreosInstall.machine_interface == interface.id).first()
            return lifecycle.success if lifecycle else None
        self.log.debug("mac: %s return None" % mac)
        return None

    def get_all_coreos_install_status(self):
        life_status_list = []
        for s in self.session.query(LifecycleCoreosInstall):
            life_status_list.append(
                {
                    "mac": s.interface.mac,
                    "fqdn": s.interface.fqdn,
                    "cidrv4": s.interface.cidrv4,
                    "success": s.success,
                    "created_date": s.created_date,
                    "updated_date": s.updated_date
                }
            )
        return life_status_list

    def get_rolling_status(self, mac):
        interface = self.session.query(MachineInterface).filter(MachineInterface.mac == mac).first()
        if interface:
            l = self.session.query(LifecycleRolling).filter(
                LifecycleRolling.machine_interface == interface.id).first()
            if l:
                return l.enable, l.strategy
        self.log.debug("mac: %s return None" % mac)
        return None, None

    def get_all_rolling_status(self):
        life_roll_list = []
        for s in self.session.query(LifecycleRolling):
            life_roll_list.append(
                {
                    "mac": s.interface.mac,
                    "fqdn": s.interface.fqdn,
                    "cidrv4": s.interface.cidrv4,
                    "enable": s.enable,
                    "created_date": s.created_date,
                    "updated_date": s.updated_date
                }
            )
        return life_roll_list


class FetchView(object):
    """
    Get the data for the User Interface View
    """
    log = logger.get_logger(__file__)

    def __init__(self, session):
        self.session = session

    def get_machines(self):
        query = self.session.query(MachineInterface).filter(MachineInterface.as_boot == True)
        data = {
            "gridColumns": [
                "Roles",
                "FQDN",
                "CIDR",
                "MAC",
                "Install",
                "LastReport",
                "LastUpdate",
                "UpToDate",
                "AutoUpdate",
            ],
            "gridData": []
        }
        for interface in query:

            coreos_install, ignition_updated_date, ignition_last_change = None, None, None
            ignition_up_to_date, lifecycle_rolling = None, None

            if interface.lifecycle_coreos_install:
                coreos_install = "Success" if interface.lifecycle_coreos_install[
                                                    0].success is True else "Failed"

            if interface.lifecycle_ignition:
                ignition_updated_date = interface.lifecycle_ignition[0].updated_date
                ignition_up_to_date = interface.lifecycle_ignition[0].up_to_date
                ignition_last_change = interface.lifecycle_ignition[0].last_change_date

            if interface.lifecycle_rolling:
                lifecycle_rolling = interface.lifecycle_rolling[0].strategy if interface.lifecycle_rolling[
                    0].enable else "Disable"

            row = {
                "Roles": ",".join([r.role for r in interface.schedule]),
                "FQDN": interface.fqdn,
                "CIDR": interface.cidrv4,
                "MAC": interface.mac,
                "Install": coreos_install,
                "LastReport": ignition_updated_date,
                "LastUpdate": ignition_last_change,
                "UpToDate": ignition_up_to_date,
                "AutoUpdate": lifecycle_rolling,
            }
            data["gridData"].append(row)
        return data
