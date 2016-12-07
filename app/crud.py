import datetime
import os

from sqlalchemy.orm import sessionmaker, subqueryload

from model import ChassisPort, Chassis, MachineInterface, Machine


class Fetch(object):
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
            return lines

        return lines

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
                    "as_boot": k.as_boot
                } for k in machine.interfaces]
            interface_boot = self.session.query(MachineInterface).filter(
                MachineInterface.machine_id == machine.id and
                MachineInterface.as_boot is True).first()

            m["boot-info"] = {
                "uuid": machine.uuid,
                "mac": interface_boot.mac
            }

            all_data.append(m)

        return all_data


class Inject(object):
    def __init__(self, engine, ignition_journal, discovery):
        sm = sessionmaker(bind=engine)
        self.session = sm()
        self.ignition_journal = ignition_journal
        self.adds = 0
        self.updates = 0

        self.discovery = discovery

        try:
            self.machine = self._machine()
            self.interfaces = self._machine_interfaces()

            self.chassis = self._chassis()
            self.chassis_port = self._chassis_port()

            self._ignition_journal()
        except Exception:
            self.session.close()
            raise

    def _machine(self):
        uuid = self.discovery["boot-info"]["uuid"]
        if len(uuid) != 36:
            raise TypeError("uuid: %s in not len(36)" % uuid)
        machine = self.session.query(Machine).filter(Machine.uuid == uuid).first()
        if machine:
            machine.updated_date = datetime.datetime.utcnow()
            self.session.add(machine)
            self.updates += 1
            return machine
        machine = Machine(uuid=uuid)
        self.session.add(machine)
        self.adds += 1
        return machine

    def _machine_interfaces(self):
        m_interfaces = self.machine.interfaces

        for i in self.discovery["interfaces"]:
            if i["mac"] and self.session.query(MachineInterface).filter(MachineInterface.mac == i["mac"]).count() == 0:
                m_interfaces.append(
                    MachineInterface(
                        name=i["name"],
                        netmask=i["netmask"],
                        mac=i["mac"],
                        ipv4=i["ipv4"],
                        cidrv4=i["cidrv4"],
                        as_boot=True if i["mac"] == self.discovery["boot-info"]["mac"] else False,
                        machine_id=self.machine.id)
                )
                self.adds += 1

        return m_interfaces

    def _chassis(self):
        chassis_list = []
        if self.discovery["lldp"]["is_file"] is False:
            return chassis_list
        for j in self.discovery["lldp"]["data"]["interfaces"]:
            chassis = self.session.query(Chassis).filter(Chassis.mac == j["chassis"]["id"]).count()
            if chassis == 0:
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
        if self.discovery["lldp"]["is_file"] is False:
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
                    self.session.commit()

                except Exception:
                    self.adds, self.updates = 0, 0
                    self.session.rollback()
                    raise
        finally:
            machine_nb = self.session.query(Machine).count()
            self.session.close()
            return machine_nb, True if self.adds else False
