import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

Base = declarative_base()


class Machine(Base):
    __tablename__ = 'machine'
    id = Column(Integer, primary_key=True, autoincrement=True)

    uuid = Column(String, nullable=False)

    interfaces = relationship("MachineInterface", lazy="joined")
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, default=None)

    def __repr__(self):
        return "<%s: %s %s %s>" % (Machine.__name__, self.uuid, self.created_date, self.updated_date)


class Healthz(Base):
    __tablename__ = 'healthz'
    id = Column(Integer, primary_key=True, autoincrement=True)

    ts = Column(Float, nullable=False)
    host = Column(String, nullable=True)


class MachineInterface(Base):
    __tablename__ = 'machine-interface'
    id = Column(Integer, primary_key=True, autoincrement=True)

    mac = Column(String, nullable=False)
    name = Column(String, nullable=False)
    netmask = Column(Integer, nullable=False)
    ipv4 = Column(String, nullable=False)
    cidrv4 = Column(String, nullable=False)
    as_boot = Column(Boolean, default=False)
    gateway = Column(String, nullable=False)

    machine_id = Column(Integer, ForeignKey('machine.id'))
    chassis_port = relationship("ChassisPort")

    schedule = relationship("Schedule")

    def __repr__(self):
        return "<%s: %s %s>" % (MachineInterface.__name__, self.mac, self.cidrv4)


class Chassis(Base):
    __tablename__ = 'chassis'
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String, nullable=False)
    mac = Column(String, nullable=False)

    ports = relationship("ChassisPort", lazy="joined")

    def __repr__(self):
        return "<%s: mac:%s name:%s>" % (Chassis.__name__, self.mac, self.name)


class ChassisPort(Base):
    __tablename__ = 'chassis-port'
    id = Column(Integer, primary_key=True, autoincrement=True)

    mac = Column(String, nullable=False)
    chassis_id = Column(Integer, ForeignKey('chassis.id'))

    machine_interface_id = Column(Integer, ForeignKey('machine-interface.id'))

    def __repr__(self):
        return "<%s: mac:%s chassis_mac:%s>" % (ChassisPort.__name__, self.mac, self.chassis_id)


class Schedule(Base):
    __tablename__ = 'schedule'

    etcd_member = "etcd-member"
    kubernetes_control_plane = "kubernetes-control-plane"
    kubernetes_node = "kubernetes-node"
    roles = [etcd_member, kubernetes_control_plane, kubernetes_node]

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    machine_interface = Column(Integer, ForeignKey('machine-interface.id'), nullable=True)

    role = Column(String, nullable=False)

    @validates('role')
    def validate_role(self, key, role_name):
        if role_name not in Schedule.roles:
            raise AttributeError("%s not in %s" % (role_name, Schedule.roles))
        return role_name
