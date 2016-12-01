from sqlalchemy.orm import sessionmaker, subqueryload

from model import ChassisPort, Chassis, MachineInterface, Machine, IgnitionJournal, JournalLine


class Fetch(object):
    def __init__(self, engine):
        sm = sessionmaker(bind=engine)
        self.session = sm()

    def _get_chassis_name(self, machine_interface):
        chassis_port = self.session.query(ChassisPort).filter(
            ChassisPort.machine_interface_mac == machine_interface.mac
        ).first()
        if chassis_port:
            chassis_name = self.session.query(Chassis).filter(
                Chassis.mac == chassis_port.chassis_mac
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
                "machine": i.machine_uuid,
                "chassis_name": self._get_chassis_name(i)
            } for i in self.session.query(MachineInterface)]

    def get_ignition_journal(self, uuid):
        for j in self.session.query(IgnitionJournal).filter(
                        IgnitionJournal.machine_uuid == uuid):
            return [l.line for l in j.lines]
        return []

    def get_all(self):
        all_data = []
        for machine in self.session.query(Machine).options(subqueryload(Machine.interfaces)):
            m = dict()
            m["interfaces"] = [
                {
                    "mac": k.mac,
                    "name": k.name,
                    "netmask": k.netmask,
                    "ipv4": k.ipv4,
                    "cidrv4": k.cidrv4,
                    "as_boot": k.as_boot} for k in machine.interfaces]
            interface_boot = self.session.query(MachineInterface).filter(
                MachineInterface.machine_uuid == machine.uuid and
                MachineInterface.as_boot is True).first()

            m["boot-info"] = {
                "uuid": machine.uuid,
                "mac": interface_boot.mac
            }

            all_data.append(m)

        return all_data


class Inject(object):
    def __init__(self, engine, discovery):
        sm = sessionmaker(bind=engine)
        self.session = sm()
        self.adds = 0

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
                        machine_uuid=self.machine.uuid)
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
            # The ChassisPort doesn't exist
            if exist == 0:

                # Get the mac address of the MachineInterface by his name inside the DiscoveryPOST
                machine_interface_mac = self.__get_mac_by_name(entry["name"])

                chassis_port = ChassisPort(
                    mac=entry["port"]["id"],
                    chassis_mac=entry["chassis"]["id"],
                    machine_interface_mac=machine_interface_mac
                )
                self.session.add(chassis_port)
                self.adds += 1
                chassis_port_list.append(chassis_port)

        return chassis_port_list

    def _ignition_journal(self):
        lines = []
        boot_id = self.discovery["boot-info"]["random-id"]
        uuid = self.discovery["boot-info"]["uuid"]
        if self.discovery["ignition-journal"] is None:
            return

        if self.session.query(IgnitionJournal).filter(
                                IgnitionJournal.boot_id == boot_id and
                                IgnitionJournal.machine_uuid == uuid).first():
            return

        ign = IgnitionJournal(
            machine_uuid=self.machine.uuid,
            boot_id=boot_id
        )
        self.session.add(ign)
        self.session.flush([ign])

        self.adds += 1
        for line in self.discovery["ignition-journal"]:
            lines.append(
                JournalLine(
                    line=line,
                    ignition_journal=ign.id
                )
            )
        self.session.add_all(lines)
        self.adds += len(lines)

    def commit_and_close(self):
        try:
            if self.adds != 0:
                try:
                    self.session.commit()

                except Exception:
                    self.adds = 0
                    self.session.rollback()
                    raise
        finally:
            machine_nb = self.session.query(Machine).count()
            self.session.close()
            return machine_nb, True if self.adds else False
