"""
Database Model for the application
"""
import datetime
import re

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

BASE = declarative_base()


def compile_regex(regex):
    """
    Compile the regex for the module constants
    :param regex:
    :return:
    """
    r = re.compile(regex)

    def match(string):
        if not re.match(r, string):
            raise LookupError("%s not valid as expected" % regex)
        return string

    return match


MAC_REGEX = compile_regex("^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$")
IPV4_REGEX = compile_regex(
    r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
UUID_REGEX = compile_regex("^([0-9A-Fa-f]{8}[-]){1}([0-9A-Fa-f]{4}[-]){3}([0-9A-Fa-f]{12})$")


class Machine(BASE):
    """
    Machine represent the Virtual machine, Physical Server
    """
    __tablename__ = 'machine'
    id = Column(Integer, primary_key=True, autoincrement=True)

    uuid = Column(String(36), nullable=False)

    interfaces = relationship("MachineInterface", lazy="joined")
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, default=None)

    @validates('uuid')
    def validate_uuid_field(self, key, uuid):
        """
        The uuid field is the same from /etc/machine-id but with '-' separators
        :param key:
        :param uuid:
        :return:
        """
        if len(uuid) != 36:
            raise LookupError("len(uuid) != 36 -> %s" % uuid)
        return UUID_REGEX(uuid)

    def __repr__(self):
        return "<%s: %s %s %s>" % (Machine.__name__, self.uuid, self.created_date, self.updated_date)


class Healthz(BASE):
    """
    Healthz is used to check the write capabilities during health checks
    """
    __tablename__ = 'healthz'
    id = Column(Integer, primary_key=True, autoincrement=True)

    ts = Column(Float, nullable=False)
    host = Column(String, nullable=True)


class MachineInterface(BASE):
    """
    The interface of each Machine
    Common interface is eth0
    """
    __tablename__ = 'machine-interface'
    id = Column(Integer, primary_key=True, autoincrement=True)

    mac = Column(String(17), nullable=False, index=True)
    name = Column(String, nullable=False)
    netmask = Column(Integer, nullable=False)
    ipv4 = Column(String(15), nullable=False)
    cidrv4 = Column(String(15 + 3), nullable=False)
    as_boot = Column(Boolean, default=False)
    gateway = Column(String(15), nullable=False)
    fqdn = Column(String, nullable=True)

    machine_id = Column(Integer, ForeignKey('machine.id'))
    chassis_port = relationship("ChassisPort")

    schedule = relationship("Schedule", backref="interface")
    lifecycle_rolling = relationship("LifecycleRolling", backref="interface")
    lifecycle_coreos_install = relationship("LifecycleCoreosInstall", backref="interface")
    lifecycle_ignition = relationship("LifecycleIgnition", backref="interface")

    @validates('mac')
    def validate_mac(self, key, mac):
        """
        :param key:
        :param mac:
        :return:
        """
        return MAC_REGEX(mac)

    @validates('ipv4')
    @validates('gateway')
    def validate_ipv4(self, key, ipv4):
        """
        Gateway and IPv4 validation
        :param key:
        :param ipv4:
        :return:
        """
        return IPV4_REGEX(ipv4)

    def __repr__(self):
        return "<%s: %s %s>" % (MachineInterface.__name__, self.mac, self.cidrv4)


class Chassis(BASE):
    """
    Chassis is the physical switch inside a DataCenter
    Reports done with Link Layer Discovery Protocol
    """
    __tablename__ = 'chassis'
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String, nullable=False)
    mac = Column(String(17), nullable=False)

    ports = relationship("ChassisPort", lazy="joined")

    @validates('mac')
    def validate_mac(self, key, mac):
        return MAC_REGEX(mac)

    def __repr__(self):
        return "<%s: mac:%s name:%s>" % (Chassis.__name__, self.mac, self.name)


class ChassisPort(BASE):
    """
    Each chassis have interfaces == port
    """
    __tablename__ = 'chassis-port'
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Some constructor doesn't return a MAC address for the ID of a Port
    mac = Column(String, nullable=False)
    chassis_id = Column(Integer, ForeignKey('chassis.id'))

    machine_interface_id = Column(Integer, ForeignKey('machine-interface.id'))

    def __repr__(self):
        return "<%s: mac:%s chassis_mac:%s>" % (ChassisPort.__name__, self.mac, self.chassis_id)


class ScheduleRoles(object):
    """
    Roles available for the Scheduler
    Roles can be stacked
    """
    etcd_member = "etcd-member"
    kubernetes_control_plane = "kubernetes-control-plane"
    kubernetes_node = "kubernetes-node"

    roles = [etcd_member, kubernetes_control_plane, kubernetes_node]


class Schedule(BASE):
    """
    Schedule is a state of a machine associated to ScheduleRoles
    """
    __tablename__ = 'schedule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    machine_interface = Column(Integer, ForeignKey('machine-interface.id'), nullable=False)

    role = Column(String(len(max(ScheduleRoles.roles, key=len))), nullable=False)

    @validates('role')
    def validate_role(self, key, role_name):
        if role_name not in ScheduleRoles.roles:
            raise LookupError("%s not in %s" % (role_name, ScheduleRoles.roles))
        return role_name


class LifecycleIgnition(BASE):
    """
    During the Lifecycle of a Machine, the state of the /usr/share/oem/coreos-install.json is POST to a dedicated Flask
    route, this table store this event and if the current Machine is up to date
    """
    __tablename__ = 'lifecycle-ignition'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    machine_interface = Column(Integer, ForeignKey('machine-interface.id'), nullable=False)

    updated_date = Column(DateTime, default=None)
    last_change_date = Column(DateTime, default=None)
    up_to_date = Column(Boolean)


class LifecycleCoreosInstall(BASE):
    """
    After the script 'coreos-install' the discovery machine POST the success / failure to a dedicated Flask route
    """
    __tablename__ = 'lifecycle-coreos-install'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    machine_interface = Column(Integer, ForeignKey('machine-interface.id'), nullable=False)

    updated_date = Column(DateTime, default=None)
    success = Column(Boolean)


class LifecycleRolling(BASE):
    """
    Allow the current machine to used the semaphore locksmithd to do a rolling update
    By kexec / reboot / poweroff
    """
    __tablename__ = 'lifecycle-rolling'
    _strategy_choice = ["reboot", "kexec", "poweroff", None]

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    machine_interface = Column(Integer, ForeignKey('machine-interface.id'), nullable=False)
    updated_date = Column(DateTime, default=None)
    enable = Column(Boolean, default=False)
    strategy = Column(String, default="kexec")

    @validates('strategy')
    def validate_role(self, key, strategy):
        if strategy not in self._strategy_choice:
            raise LookupError("%s not in %s" % (strategy, self._strategy_choice))
        return strategy
