from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Machine(Base):
    __tablename__ = 'machine'
    uuid = Column(String, primary_key=True, autoincrement=False)

    interfaces = relationship("MachineInterface", lazy="joined")

    def __repr__(self):
        return "<%s: %s>" % (Machine.__name__, self.uuid)


class MachineInterface(Base):
    __tablename__ = 'machine-interface'

    mac = Column(String, nullable=False, primary_key=True, autoincrement=False)
    name = Column(String, nullable=False)
    netmask = Column(Integer, nullable=False)
    ipv4 = Column(String, nullable=False)
    cidrv4 = Column(String, nullable=False)
    as_boot = Column(Boolean, default=False)

    machine_uuid = Column(Integer, ForeignKey('machine.uuid'))
    chassis_port = relationship("ChassisPort")

    def __repr__(self):
        return "<%s: %s %s>" % (MachineInterface.__name__, self.mac, self.cidrv4)


class Chassis(Base):
    __tablename__ = 'chassis'

    name = Column(String, nullable=False)
    mac = Column(String, nullable=False, primary_key=True)

    ports = relationship("ChassisPort", lazy="joined")

    def __repr__(self):
        return "<%s: %s %s>" % (Chassis.__name__, self.mac, self.name)


class ChassisPort(Base):
    __tablename__ = 'chassis-port'

    mac = Column(String, primary_key=True, autoincrement=False)
    chassis_mac = Column(String, ForeignKey('chassis.mac'))

    machine_interface_mac = Column(String, ForeignKey('machine-interface.mac'))

    def __repr__(self):
        return "<%s: %s %s>" % (ChassisPort.__name__, self.mac, self.chassis_mac)


class Inject(object):
    def __init__(self, session, discovery):
        self.session = session
        self.adds = 0
        self.discovery = discovery

        self.machine = self._machine()
        self.interfaces = self._machine_interfaces()

        self.chassis = self._chassis()
        self.chassis_port = self._chassis_port()

    def _machine(self):
        uuid = self.discovery["boot-info"]["uuid"]
        machine = self.session.query(Machine).filter(Machine.uuid == uuid).first()
        if machine:
            return machine
        machine = Machine(uuid=uuid)
        self.session.add(machine)
        self.adds += 1
        return machine

    def _machine_interfaces(self):
        m_interfaces = self.machine.interfaces
        if m_interfaces:
            return m_interfaces

        for i in self.discovery["interfaces"]:
            if i["mac"] and i["mac"] not in [k.mac for k in m_interfaces]:
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
        for j in self.discovery["lldp"]["data"]["interfaces"]:
            chassis = self.session.query(Chassis).filter(Chassis.mac == j["chassis"]["id"]).first()
            if not chassis:
                chassis = Chassis(
                    name=j["chassis"]["name"],
                    mac=j["chassis"]["id"]
                )
                self.session.add(chassis)
                self.adds += 1
            chassis_list.append(chassis)

        return chassis_list

    def _chassis_port(self):
        chassis_port_list = []
        for j in self.discovery["lldp"]["data"]["interfaces"]:
            for machine_interface in self.machine.interfaces:
                if machine_interface.name == j["name"] and \
                        not self.session.query(ChassisPort.mac == j["port"]["id"]).first():
                    chassis = self.session.query(Chassis).filter(Chassis.mac == j["chassis"]["id"]).first()
                    chassis_port = ChassisPort(
                        mac=j["port"]["id"],
                        chassis_mac=chassis.mac,
                        machine_interface_mac=machine_interface.mac
                    )
                    self.session.add(chassis_port)
                    self.adds += 1
                    chassis_port_list.append(chassis_port)
        return chassis_port_list

    def commit(self):
        if self.adds != 0:
            self.session.commit()
