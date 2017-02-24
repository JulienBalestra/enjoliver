import datetime
import os

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, subqueryload

import logger
from model import ChassisPort, Chassis, MachineInterface, Machine, Healthz, Schedule, ScheduleRoles, Lifecycle


class FetchDiscovery(object):
    def __init__(self, engine, ignition_journal):
        sm = sessionmaker(bind=engine)
        self.session = sm()
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

    def close(self):
        self.session.close()

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
                "chassis_name": self._get_chassis_name(i)
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
            ig = os.listdir(self.ignition_journal)
            for uuid in ig:
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
                    "gateway": k.gateway
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


def health_check(engine, ts, who):
    health = False
    sm = sessionmaker(bind=engine)
    session = sm()
    try:
        h = Healthz()
        h.ts = ts
        h.host = who
        session.add(h)
        session.commit()
        query_ts = session.query(Healthz).filter(Healthz.ts == ts).all()
        if query_ts[0].ts != ts:
            raise AssertionError("%s not in %s" % (ts, query_ts))
        session.query(Healthz).filter(Healthz.ts < ts).delete()
        session.commit()
        health = True
    finally:
        session.close()
    return health


class InjectDiscovery(object):
    log = logger.get_logger(__file__)

    def __init__(self, engine, ignition_journal, discovery):
        sm = sessionmaker(bind=engine)
        self.session = sm()
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
            self.log.error("raise: %s %s %s %s -> %s" % (step, type(e), e, e.message, self.discovery))
            self.session.close()
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

    def _machine_interfaces(self):
        m_interfaces = self.machine.interfaces

        for i in self.discovery["interfaces"]:
            # TODO make only one query instead of many
            if i["mac"] and self.session.query(MachineInterface).filter(MachineInterface.mac == i["mac"]).count() == 0:
                self.log.debug("mac not in db: %s adding" % i["mac"])
                m_interfaces.append(
                    MachineInterface(
                        name=i["name"],
                        netmask=i["netmask"],
                        mac=i["mac"],
                        ipv4=i["ipv4"],
                        cidrv4=i["cidrv4"],
                        as_boot=True if i["mac"] == self.discovery["boot-info"]["mac"] else False,
                        gateway=i["gateway"],
                        machine_id=self.machine.id)
                )
                self.adds += 1

        return m_interfaces

    def _chassis(self):
        chassis_list = []
        if self.discovery["lldp"]["is_file"] is False or not self.discovery["lldp"]["data"]["interfaces"]:
            return chassis_list
        for j in self.discovery["lldp"]["data"]["interfaces"]:
            chassis = self.session.query(Chassis).filter(Chassis.mac == j["chassis"]["id"]).count()
            if chassis == 0:
                self.log.debug("chassis %s %s not in db" % (j["chassis"]["name"], j["chassis"]["id"]))
                chassis = Chassis(
                    name=j["chassis"]["name"],
                    mac=j["chassis"]["id"]
                )
                self.session.add(chassis)
                self.adds += 1
            chassis_list.append(chassis)

        return chassis_list

    def __get_mac_by_name(self, name):
        for i in self.discovery["interfaces"]:
            if i["name"] == name:
                return i["mac"]

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

    def commit_and_close(self):
        try:
            if self.adds != 0 or self.updates != 0:
                try:
                    self.log.debug("commiting")
                    self.session.commit()

                except Exception as e:
                    self.log.error("%s %s %s adds=%s updates=%s" % (type(e), e, e.message, self.adds, self.updates))
                    self.adds, self.updates = 0, 0
                    self.log.warning("rollback the sessions")
                    self.session.rollback()
                    raise
        finally:
            machine_nb = self.session.query(Machine).count()
            self.log.debug("closing")
            self.session.close()
            return machine_nb, True if self.adds else False


class FetchSchedule(object):
    def __init__(self, engine):
        sm = sessionmaker(bind=engine)
        self.session = sm()

    def get_schedules(self):
        s = self.session.query(Schedule, MachineInterface).join(
            MachineInterface).all()

        r = {}
        for i in s:
            try:
                r[i[1].mac] += [i[0].role]
            except KeyError:
                r[i[1].mac] = [i[0].role]

        return r

    def get_roles_by_mac_selector(self, mac):
        s = self.session.query(Schedule).join(MachineInterface).filter(MachineInterface.mac == mac).all()
        r = [k.role for k in s]
        return r

    def get_available_machines(self):
        s = self.session.query(MachineInterface).filter(
            MachineInterface.schedule == None, MachineInterface.as_boot == True).all()
        l = []
        for i in s:
            l.append(
                {
                    "mac": i.mac,
                    "ipv4": i.ipv4,
                    "cidrv4": i.cidrv4,
                    "gateway": i.gateway,
                    "as_boot": i.as_boot,
                    "name": i.name,
                    "netmask": i.netmask,
                    "roles": [k.role for k in i.schedule]
                }
            )
        return l

    def get_role(self, role):
        s = self.session.query(Schedule).filter(Schedule.role == role).all()
        l = []
        for i in s:
            l.append({
                "mac": i.interface.mac,
                "ipv4": i.interface.ipv4,
                "cidrv4": i.interface.cidrv4,
                "gateway": i.interface.gateway,
                "as_boot": i.interface.as_boot,
                "name": i.interface.name,
                "netmask": i.interface.netmask,
                "role": i.role,
                "created_date": i.created_date
            })

        return l

    def get_roles(self, *args):
        s = self.session.query(MachineInterface).join(Schedule).filter(
            Schedule.role.in_(args)
        ).group_by(MachineInterface.id).having(func.count(MachineInterface.id) == len(args)).all()
        l = []
        for i in s:
            l.append(
                {
                    "mac": i.mac,
                    "ipv4": i.ipv4,
                    "cidrv4": i.cidrv4,
                    "gateway": i.gateway,
                    "as_boot": i.as_boot,
                    "name": i.name,
                    "netmask": i.netmask,
                    "roles": [k.role for k in i.schedule]
                }
            )
        return l

    def get_role_ip_list(self, role):
        s = self.session.query(Schedule).filter(Schedule.role == role).all()

        return [k.interface.ipv4 for k in s]

    def close(self):
        self.session.close()


class InjectSchedule(object):
    log = logger.get_logger(__file__)

    def __init__(self, engine, data):
        sm = sessionmaker(bind=engine)
        self.session = sm()
        self.adds = 0
        self.updates = 0

        self.data = data
        self.mac = self.data["selector"]["mac"]

        self.interface = self.session.query(MachineInterface).filter(MachineInterface.mac == self.mac).first()
        if not self.interface:
            m = "mac: '%s' unknown in db" % self.mac
            self.log.error(m)
            self.session.close()
            raise AttributeError(m)
        self.log.info("mac: %s" % self.mac)

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

    def commit_and_close(self):
        try:
            if self.adds != 0 or self.updates != 0:
                try:
                    self.log.debug("commiting")
                    self.session.commit()

                except Exception as e:
                    self.log.error("%s %s %s adds=%s updates=%s" % (type(e), e, e.message, self.adds, self.updates))
                    self.adds, self.updates = 0, 0
                    self.log.warning("rollback the sessions")
                    self.session.rollback()
                    raise
        finally:
            roles_rapport = {}
            for r in ScheduleRoles.roles:
                roles_rapport[r] = self.session.query(Schedule).filter(Schedule.role == r).count()
            self.log.debug("closing")
            self.session.close()
            return roles_rapport, True if self.adds else False


class InjectLifecycle(object):
    log = logger.get_logger(__file__)

    def __init__(self, engine, request_raw_query):
        sm = sessionmaker(bind=engine)
        self.session = sm()
        self.adds = 0
        self.updates = 0

        self.mac = self._get_mac_from_query(request_raw_query)

        self.interface = self.session.query(MachineInterface).filter(MachineInterface.mac == self.mac).first()
        if not self.interface:
            m = "mac: '%s' unknown in db" % self.mac
            self.log.error(m)
            self.session.close()
            raise AttributeError(m)
        self.log.info("mac: %s" % self.mac)

    @staticmethod
    def _get_mac_from_query(request_raw_query):
        mac = ""
        s = request_raw_query.split("&")
        for param in s:
            if "mac=" in param:
                mac = param.replace("mac=", "")
        if not mac:
            raise AttributeError("%s is not parsable" % request_raw_query)
        return mac.replace("-", ":")

    def refresh_lifecycle(self, up_to_date):
        l = self.session.query(Lifecycle).filter(
            Lifecycle.machine_interface == self.interface.id).first()
        if not l:
            l = Lifecycle(
                machine_interface=self.interface.id,
                up_to_date=up_to_date
            )
        else:
            l.up_to_date = up_to_date
            l.updated_date = datetime.datetime.utcnow()
        self.session.add(l)
        self.session.commit()
        self.session.close()


class FetchLifecycle(object):
    def __init__(self, engine):
        sm = sessionmaker(bind=engine)
        self.session = sm()

    def get_update_status(self, mac):
        interface = self.session.query(MachineInterface).filter(MachineInterface.mac == mac).first()
        if interface:
            l = self.session.query(Lifecycle).filter(
                Lifecycle.machine_interface == interface.id).first()
            return l.up_to_date
        return None

    def get_all_updated_status(self):
        l = []
        for s in self.session.query(Lifecycle).all():
            l.append(
                {
                    "up-to-date": s.up_to_date,
                    "created_date": s.created_date,
                    "updated_date": s.updated_date
                }
            )
        return l

    def close(self):
        self.session.close()
