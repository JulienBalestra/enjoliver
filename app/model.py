import datetime
import re

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, SmallInteger
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

Base = declarative_base()


def compile_regex(regex):
    r = re.compile(regex)

    def match(string):
        if not re.match(r, string):
            raise LookupError("%s not valid as expected" % regex)
        return string

    return match

mac_regex = compile_regex("^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$")
ipv4_regex = compile_regex(
    "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
uuid_regex = compile_regex("^([0-9A-Fa-f]{8}[-]){1}([0-9A-Fa-f]{4}[-]){3}([0-9A-Fa-f]{12})$")


class Machine(Base):
    __tablename__ = 'machine'
    id = Column(Integer, primary_key=True, autoincrement=True)

    uuid = Column(String(36), nullable=False)

    interfaces = relationship("MachineInterface", lazy="joined")
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, default=None)

    @validates('uuid')
    def validate_uuid_field(self, key, uuid):
        if len(uuid) != 36:
            raise LookupError("len(uuid) != 36 -> %s" % uuid)
        return uuid_regex(uuid)

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

    mac = Column(String(17), nullable=False)
    name = Column(String, nullable=False)
    netmask = Column(SmallInteger, nullable=False)
    ipv4 = Column(String(15), nullable=False)
    cidrv4 = Column(String(15 + 3), nullable=False)
    as_boot = Column(Boolean, default=False)
    gateway = Column(String(15), nullable=False)

    machine_id = Column(Integer, ForeignKey('machine.id'))
    chassis_port = relationship("ChassisPort")

    schedule = relationship("Schedule", backref="interface")

    @validates('mac')
    def validate_mac(self, key, mac):
        return mac_regex(mac)

    @validates('ipv4')
    @validates('gateway')
    def validate_ipv4(self, key, ipv4):
        return ipv4_regex(ipv4)

    def __repr__(self):
        return "<%s: %s %s>" % (MachineInterface.__name__, self.mac, self.cidrv4)


class Chassis(Base):
    __tablename__ = 'chassis'
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String, nullable=False)
    mac = Column(String(17), nullable=False)

    ports = relationship("ChassisPort", lazy="joined")

    @validates('mac')
    def validate_mac(self, key, mac):
        return mac_regex(mac)

    def __repr__(self):
        return "<%s: mac:%s name:%s>" % (Chassis.__name__, self.mac, self.name)


class ChassisPort(Base):
    __tablename__ = 'chassis-port'
    id = Column(Integer, primary_key=True, autoincrement=True)

    mac = Column(String(17), nullable=False)
    chassis_id = Column(Integer, ForeignKey('chassis.id'))

    machine_interface_id = Column(Integer, ForeignKey('machine-interface.id'))

    def __repr__(self):
        return "<%s: mac:%s chassis_mac:%s>" % (ChassisPort.__name__, self.mac, self.chassis_id)

    @validates('mac')
    def validate_mac(self, key, mac):
        return mac_regex(mac)


class Schedule(Base):
    __tablename__ = 'schedule'

    etcd_member = "etcd-member"
    kubernetes_control_plane = "kubernetes-control-plane"
    kubernetes_node = "kubernetes-node"
    roles = [etcd_member, kubernetes_control_plane, kubernetes_node]

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    machine_interface = Column(Integer, ForeignKey('machine-interface.id'), nullable=True)

    role = Column(String(len(max(roles, key=len))), nullable=False)

    @validates('role')
    def validate_role(self, key, role_name):
        if role_name not in Schedule.roles:
            raise LookupError("%s not in %s" % (role_name, Schedule.roles))
        return role_name
