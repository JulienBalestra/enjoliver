import abc
import json
import random
import socket
import time
import urllib2

import ipaddr

import generator
import logger


class CommonScheduler(object):
    """
    Base class to create profiles with deps
    """
    __metaclass__ = abc.ABCMeta

    log = logger.get_logger(__file__)

    ipam_multiplier = 256
    ipam_ips = 254

    etcd_initial_cluster_set = set()

    apply_deps_tries = 100
    apply_deps_delay = 60

    def get_dns_name(self, host_ipv4, default=None):
        """
        Get the DNS name by IPv4 address, fail to a default name
        :param host_ipv4:
        :param default: param returned if socket exception
        :return:
        """
        try:
            t = socket.gethostbyaddr(host_ipv4)
            return t[0]
        except socket.herror:
            self.custom_log(self.get_dns_name.__name__,
                            "fail to get host by addr setting default provided: %s" % default, "warning")
            return default

        except Exception as e:
            self.custom_log(self.get_dns_name.__name__, "fail to get host by addr: %s %s" % (e, e.message), "error")
            raise

    @staticmethod
    def cni_ipam(host_cidrv4, host_gateway):
        """
        With the class variables provide a way to generate a static host-local ipam
        :param host_cidrv4:
        :param host_gateway:
        :return: dict
        """
        host = ipaddr.IPNetwork(host_cidrv4)
        ip_cut = int(host.ip.__str__().split(".")[-1])
        sub = ipaddr.IPNetwork(host.network).ip + (ip_cut * CommonScheduler.ipam_multiplier)
        rs = sub + 1
        re = sub + CommonScheduler.ipam_ips
        ipam = {
            "type": "host-local",
            "subnet": "%s/%s" % (host.network.__str__(), host.prefixlen),
            "rangeStart": rs.__str__(),
            "rangeEnd": re.__str__(),
            "gateway": host_gateway,
            "routes": [{"dst": "0.0.0.0/0"}]
        }
        return ipam

    def custom_log(self, func_name, message, level="info"):
        """
        Custom log method
        :param func_name: func.__name__
        :param message: message to display
        :param level: log level (will be lower() anyway)
        :return: None
        """
        if level.lower() == "debug":
            self.log.debug("%s.%s %s" % (self.__name__, func_name, message))
        elif level.lower() == "warning":
            self.log.warning("%s.%s %s" % (self.__name__, func_name, message))
        elif level.lower() == "error":
            self.log.warning("%s.%s %s" % (self.__name__, func_name, message))
        else:
            self.log.info("%s.%s %s" % (self.__name__, func_name, message))

    def get_extra_selectors(self, extra_selectors):
        """
        Extra selectors are passed to Bootcfg
        :param extra_selectors: dict
        :return:
        """
        if extra_selectors:
            if type(extra_selectors) is dict:
                self.custom_log(self.get_extra_selectors.__name__, "extra selectors: %s" % extra_selectors)
                return extra_selectors

            self.custom_log(self.get_extra_selectors.__name__, "invalid extra selectors: %s" % extra_selectors,
                            level="error")
            raise TypeError("%s is not type dict" % extra_selectors)

        self.custom_log(self.get_extra_selectors.__name__, "no extra selectors",
                        level="debug")
        return {}

    @staticmethod
    def get_machine_tuple(discovery):
        """
        Get inside discovery dict the ipv4, mac, cidrv4, gateway
        :param discovery: dict
        :return: ipv4, mac, cidrv4, gateway
        """
        mac = discovery["boot-info"]["mac"]
        ipv4, cidrv4, gateway = None, None, None
        nb_interfaces = len(discovery["interfaces"])
        for n, i in enumerate(discovery["interfaces"]):
            if i["mac"] == mac:
                ipv4 = i["ipv4"]
                cidrv4 = i["cidrv4"]
                gateway = i["gateway"]
                CommonScheduler.log.debug("%d/%d %s matching in %s" % (n + 1, nb_interfaces, mac, str(i)))
                try:
                    if i["as_boot"] is False:
                        CommonScheduler.log.warning(
                            "interface %s is the 'boot-info' 'mac' but 'as_boot' is False" % str(i))
                except KeyError:
                    CommonScheduler.log.warning("interface without key 'as_boot'")
            else:
                CommonScheduler.log.debug("%d/%d %s not matching in %s" % (n + 1, nb_interfaces, mac, str(i)))
        if ipv4 is None:
            message = "%s Lookup failed in %s" % (mac, discovery)
            CommonScheduler.log.error(message)
            raise LookupError(message)
        return ipv4, mac, cidrv4, gateway

    @staticmethod
    def fetch_discovery(api_uri):
        """
        HTTP Get to the <api_uri>/discovery
        :param api_uri: str
        :return: list of interfaces
        """
        CommonScheduler.log.info("fetch %s" % api_uri)
        content = urllib2.urlopen("%s/discovery" % api_uri)
        response_body = content.read()
        content.close()
        interfaces = json.loads(response_body)
        CommonScheduler.log.info("fetch done")
        return interfaces

    @abc.abstractmethod
    def apply(self):
        """
        Entrypoint to apply the schedule plan
        >>> sch = CommonScheduler()
        >>> sch.apply()
        :return: True if it's a number require
            (3 members for Etcd), int number of effective apply (Etcd Proxy)
        """

    def apply_dep(self):
        for t in xrange(self.apply_deps_tries):
            if self._dep_instance.apply() is True:
                return True
            time.sleep(self.apply_deps_delay)

        self.custom_log(self.apply_dep.__name__, "timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries), "error")
        raise RuntimeError("timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries))

    @property
    def etcd_initial_cluster(self):
        """
        The environment variable for the etcd initial cluster
        static1=http://1.1.1.1:2380,static2=http://2.2.2.2:2380,static3=http://3.3.3.3:2380
        :return: str
        """
        if len(self.etcd_initial_cluster_set) == 0:
            self.log.warning("len of etcd_initial_cluster_list == 0")
        l = list(self.etcd_initial_cluster_set)
        random.shuffle(l)
        return ",".join(l)

    @abc.abstractproperty
    def ip_list(self):
        """
        List of IP address
        :return: list
        """

    @abc.abstractproperty
    def done_list(self):
        """
        List of set of data provides by
        >>> CommonScheduler.get_machine_tuple(discovery={})
        :return: list of set
        """

    @abc.abstractproperty
    def wide_done_list(self):
        """
        The done_list of the current instances and his dep's done_list
        :return: list of ips
        """


class K8sNodeScheduler(CommonScheduler):
    __name__ = "K8sNodeScheduler"
    apply_deps_delay = 6
    apply_deps_tries = apply_deps_delay * 50

    def __init__(self,
                 dep_instance,
                 ignition_node,
                 apply_first=False,
                 extra_selectors=None):

        self.log.debug("instancing %s" % self.__name__)
        self._dep_instance = dep_instance

        if isinstance(self._dep_instance, K8sControlPlaneScheduler):
            if apply_first is True:
                self.apply_dep()

        elif isinstance(self._dep_instance, EtcdMemberK8sControlPlaneScheduler):
            if apply_first is True:
                raise NotImplementedError

        else:
            raise AttributeError("%s not a instanceof(%s||%s): type(%s)" % (
                "k8s_control_plane", K8sControlPlaneScheduler.__name__,
                EtcdMemberK8sControlPlaneScheduler.__name__,
                type(self._dep_instance)))

        self._ignition_node = ignition_node
        self.api_endpoint = self._dep_instance.api_endpoint
        self.bootcfg_prefix = self._dep_instance.bootcfg_prefix
        self.bootcfg_path = self._dep_instance.bootcfg_path
        self._extra_selectors = self.get_extra_selectors(extra_selectors)

        # State
        self._done = set()
        self._pending = set()

    def _fall_back(self, discovery):
        if len(self._pending) != 0:
            raise AssertionError("len(self._pending_k8s_node) != 0 -> %s" % str(self._pending))

        if len(discovery) > len(self.wide_done_list):
            for machine in discovery:
                ip_mac = self.get_machine_tuple(machine)
                if ip_mac in self._done:
                    self.custom_log(self._fall_back.__name__,
                                    "Skip because K8s Node %s" % str(ip_mac))
                elif ip_mac in self.wide_done_list:
                    self.custom_log(self._fall_back.__name__,
                                    "Skip because in Wide Schedule %s" % str(ip_mac))
                else:
                    self.custom_log(self._fall_back.__name__,
                                    "Pending K8s Node %s" % str(ip_mac))
                    self._pending.add(ip_mac)
        else:
            self.custom_log(self._fall_back.__name__,
                            "no machine 0 %s" % len(self._pending))

    def _apply(self):
        self.custom_log(self._apply.__name__, "in progress...")

        marker = "%s%snode" % (self.bootcfg_prefix, "k8s")

        base = len(self._done)
        new_pending = set()
        for i, m in enumerate(self._pending):
            # m = (IPv4, MAC, CIDRv4, Gateway)
            s = {"mac": m[1]}
            hostname = self.get_dns_name(m[0], "k8s-node-%d" % i)
            s.update(self._extra_selectors)
            i += base
            gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_node,
                bootcfg_path=self.bootcfg_path,
                selector=s,
                extra_metadata={
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_advertise_client_urls": "http://%s:2379" % m[0],
                    "etcd_proxy": "on",
                    "kubelet_ip": "%s" % m[0],
                    "kubelet_name": "%s" % m[0],
                    "k8s_endpoint": ",".join(self._dep_instance.k8s_endpoint),
                    "hostname": hostname,
                    "cni": json.dumps(self.cni_ipam(m[2], m[3]))
                }
            )
            gen.dumps()
            self._done.add(m)
            new_pending = self._pending - self._done
            self.custom_log(self._apply.__name__, "selector {mac: %s}" % m[1])

        if self._pending - self._done:
            message = "self._pending_k8s_node - self._done_k8s_node have to return an empty set"
            self.custom_log(self._apply.__name__, message, level="error")
            raise AssertionError(message)
        self._pending = new_pending

    def apply(self):
        discovery = self.fetch_discovery(self.api_endpoint)
        self._fall_back(discovery)
        if len(self._pending) > 0:
            self._apply()

        self.custom_log(self.apply.__name__, "total %d" % len(self._done))
        return len(self._done)

    @property
    def ip_list(self):
        return [k[0] for k in self._done]

    @property
    def done_list(self):
        return [k for k in self._done]

    @property
    def wide_done_list(self):
        return self.done_list + self._dep_instance.wide_done_list


class EtcdProxyScheduler(K8sNodeScheduler):
    __name__ = "EtcdProxyScheduler"

    def __init__(self,
                 dep_instance,
                 ignition_proxy,
                 apply_first=False,
                 extra_selectors=None):

        self.log.debug("instancing %s" % self.__name__)
        self._dep_instance = dep_instance

        if isinstance(self._dep_instance, EtcdMemberScheduler) is False:
            message = "%s not a instanceof(%s)" % (
                "etcd_member_instance", EtcdMemberScheduler.__name__)
            self.log.error(message)
            raise AttributeError(message)

        if apply_first is True:
            self.apply_dep()

        self._ignition_proxy = ignition_proxy
        self.api_endpoint = self._dep_instance.api_endpoint
        self.bootcfg_prefix = self._dep_instance.bootcfg_prefix
        self.bootcfg_path = self._dep_instance.bootcfg_path
        self._extra_selectors = self.get_extra_selectors(extra_selectors)

        # State
        self._done = set()
        self._pending = set()

    def _apply(self):
        self.custom_log(self._apply.__name__, "in progress...")

        marker = "%s%sproxy" % (self.bootcfg_prefix, "e")  # e for Etcd

        base = len(self._done)
        new_pending = set()
        for i, m in enumerate(self._pending):
            # m = (IPv4, MAC, CIDRv4, Gateway)
            s = {"mac": m[1]}
            s.update(self._extra_selectors)
            hostname = self.get_dns_name(m[0], "etcd-proxy-%d" % i)
            i += base
            gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_proxy,
                bootcfg_path=self.bootcfg_path,
                selector=s,
                extra_metadata={
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_advertise_client_urls": "http://%s:2379" % m[0],
                    "etcd_proxy": "on",
                    "hostname": hostname,
                    "cni": json.dumps(self.cni_ipam(m[2], m[3]))
                }
            )
            gen.dumps()
            self._done.add(m)
            new_pending = self._pending - self._done
            self.custom_log(self._apply.__name__, "selector {mac: %s}" % m[1])

        if self._pending - self._done:
            message = "self._pending_etcd_proxy - self._done_etcd_proxy have to return an empty set"
            self.custom_log(self._apply.__name__, message, level="error")
            raise AssertionError(message)
        self._pending = new_pending


class K8sControlPlaneScheduler(CommonScheduler):
    __name__ = "K8sControlPlaneScheduler"

    apply_deps_delay = 6
    apply_deps_tries = apply_deps_delay * 50

    control_plane_nb = 3
    api_server_port = 8080

    def __init__(self,
                 dep_instance,
                 ignition_control_plane,
                 apply_first=False,
                 extra_selectors=None):
        self.log.debug("instancing %s" % self.__name__)
        self._dep_instance = dep_instance

        if isinstance(self._dep_instance, EtcdMemberScheduler) is False:
            message = "%s not a instanceof(%s)" % ("etcd_member_instance", EtcdMemberScheduler.__name__)
            self.log.error(message)
            raise AttributeError(message)

        if apply_first is True:
            self.apply_dep()

        self._ignition_control_plane = ignition_control_plane
        self.api_endpoint = self._dep_instance.api_endpoint
        self.bootcfg_prefix = self._dep_instance.bootcfg_prefix
        self.bootcfg_path = self._dep_instance.bootcfg_path
        self._extra_selectors = self.get_extra_selectors(extra_selectors)

        # State
        self._done = set()
        self._pending = set()

    def _fifo_control_plane_simple(self, discovery):
        if not discovery or len(discovery) == 0:
            self.custom_log(self._fifo_control_plane_simple.__name__,
                            "no machine 0/%d" % self.control_plane_nb)
            return self._pending

        elif len(discovery) < self.control_plane_nb:
            self.custom_log(self._fifo_control_plane_simple.__name__,
                            "not enough machines %d/%d" % (
                                len(discovery), self.control_plane_nb))
            return self._pending

        else:
            for machine in discovery:
                ip_mac = self.get_machine_tuple(machine)
                if ip_mac in self._done:
                    self.custom_log(self._fifo_control_plane_simple.__name__,
                                    "WARNING Skip because K8s Control Plane  %s" % str(ip_mac))
                elif ip_mac in self.wide_done_list:
                    self.custom_log(self._fifo_control_plane_simple.__name__,
                                    "Skip because Wide Schedule %s" % str(ip_mac))
                elif len(self._pending) < self.control_plane_nb:
                    self.custom_log(self._fifo_control_plane_simple.__name__,
                                    "Pending K8s Control Plane %s" % str(ip_mac))
                    self._pending.add(ip_mac)
                else:
                    break

        self.custom_log(self._fifo_control_plane_simple.__name__,
                        "enough machines %d/%d" % (len(discovery), self.control_plane_nb))
        return self._pending

    def _apply(self):
        self.custom_log(self._apply.__name__, "in progress...")

        marker = "%s%scontrol-plane" % (self.bootcfg_prefix, "k8s")

        new_pending = set()
        for i, m in enumerate(self._pending):
            # m = (IPv4, MAC, CIDRv4, Gateway)
            s = {"mac": m[1]}
            hostname = self.get_dns_name(m[0], "k8s-control-plane-%d" % i)
            s.update(self._extra_selectors)
            gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_control_plane,
                bootcfg_path=self.bootcfg_path,
                selector=s,
                extra_metadata={
                    # Etcd Proxy
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_advertise_client_urls": "http://%s:2379" % m[0],
                    "etcd_proxy": "on",
                    # K8s Control Plane
                    "k8s_apiserver_count": self.control_plane_nb,
                    "kubelet_ip": "%s" % m[0],
                    "kubelet_name": "%s" % m[0],
                    "k8s_advertise_ip": "%s" % m[0],
                    "hostname": hostname,
                    "cni": json.dumps(self.cni_ipam(m[2], m[3]))
                }
            )
            gen.dumps()
            self._done.add(m)
            new_pending = self._pending - self._done
            self.custom_log(self._apply.__name__, "selector {mac: %s}" % m[1])

        if self._pending - self._done:
            message = "self._apply_control_plane - self._done_control_plane have to return an empty set"
            self.custom_log(self._apply.__name__, message, level="error")
            raise AssertionError(message)
        self._pending = new_pending

    def apply(self):
        self.apply_dep()
        # K8s Control Plane
        if len(self._done) < self.control_plane_nb:
            discovery = self.fetch_discovery(self.api_endpoint)
            self._fifo_control_plane_simple(discovery)
            if len(self._pending) == self.control_plane_nb:
                self._apply()

        else:
            self.custom_log(self.apply.__name__, "already complete")
            return True

        if len(self._done) < self.control_plane_nb:
            self.custom_log(self.apply.__name__, "uncomplete")
            return False
        else:
            self.custom_log(self.apply.__name__, "complete")
            return True

    @property
    def k8s_endpoint(self):
        e = ["http://%s:%d" % (k[0], self.api_server_port) for k in self._done]
        random.shuffle(e)
        return e

    @property
    def ip_list(self):
        return [k[0] for k in self._done]

    @property
    def done_list(self):
        return [k for k in self._done]

    @property
    def wide_done_list(self):
        return self.done_list + self._dep_instance.wide_done_list


class EtcdMemberK8sControlPlaneScheduler(CommonScheduler):
    etcd_members_nb = 3
    __name__ = "EtcdMemberK8sControlPlaneScheduler"
    etcd_name = "static"  # basename

    control_plane_nb = 3
    api_server_port = 8080

    def __init__(self,
                 api_endpoint, bootcfg_path,
                 ignition_member,
                 bootcfg_prefix="",
                 extra_selectors=None):
        self.log.debug("instancing %s" % self.__name__)
        # self.etcd_initial_cluster_set = set()

        self.api_endpoint = api_endpoint
        self.bootcfg_path = bootcfg_path
        self.bootcfg_prefix = bootcfg_prefix

        # Etcd member area
        self._ignition_member = ignition_member
        self._pending_etcd_member = set()
        self._done_etcd_member = set()
        self._extra_selectors = self.get_extra_selectors(extra_selectors)

        # Kubernetes
        self._done = set()
        self._pending = set()

    def _fifo_members_simple(self, discovery):

        if not discovery or len(discovery) == 0:
            self.custom_log(self._fifo_members_simple.__name__, "no machine 0/%d" % self.etcd_members_nb)
            return self._pending_etcd_member

        elif len(discovery) < self.etcd_members_nb:
            self.custom_log(self._fifo_members_simple.__name__,
                            "not enough machines %d/%d" % (len(discovery), self.etcd_members_nb))
            return self._pending_etcd_member

        else:
            for machine in discovery:
                ip_mac = self.get_machine_tuple(machine)
                if len(self._pending_etcd_member) < self.etcd_members_nb:
                    self._pending_etcd_member.add(ip_mac)
                    self.custom_log(self._fifo_members_simple.__name__,
                                    "added machine %s %d/%d" % (
                                        ip_mac, len(self._pending_etcd_member), self.etcd_members_nb))
                else:
                    break

        self.custom_log(self._fifo_members_simple.__name__,
                        "enough machines %d/%d" % (len(discovery), self.etcd_members_nb))
        return self._pending_etcd_member

    def _apply(self):
        self.custom_log(self._apply.__name__, "in progress...")

        marker = "%s%smember" % (self.bootcfg_prefix, "e")  # e for Etcd

        if self.etcd_initial_cluster_set:
            self.custom_log(
                self._apply.__name__, "self.etcd_initial_cluster_set is not empty", level="error")
            raise AttributeError("self.etcd_initial_cluster_set is not empty: %s" % self.etcd_initial_cluster_set)

        for i, m in enumerate(self._pending_etcd_member):
            self.etcd_initial_cluster_set.add("%s%d=http://%s:2380" % (self.etcd_name, i, m[0]))

        for i, m in enumerate(self._pending_etcd_member):
            # m = (IPv4, MAC, CIDRv4, Gateway)
            s = {"mac": m[1]}
            hostname = self.get_dns_name(m[0], "k8s-control-plane-%d" % i)
            s.update(self._extra_selectors)
            gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_member,
                bootcfg_path=self.bootcfg_path,
                selector=s,
                extra_metadata={
                    "etcd_name": "%s%d" % (self.etcd_name, i),
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_initial_advertise_peer_urls": "http://%s:2380" % m[0],
                    "etcd_advertise_client_urls": "http://%s:2379" % m[0],
                    # K8s Control Plane
                    "k8s_apiserver_count": self.control_plane_nb,
                    "kubelet_ip": "%s" % m[0],
                    "kubelet_name": "%s" % m[0],
                    "k8s_advertise_ip": "%s" % m[0],
                    "hostname": hostname,
                    "cni": json.dumps(self.cni_ipam(m[2], m[3]))
                }
            )
            gen.dumps()
            self._done_etcd_member.add(m)
            self._done.add(m)
            self.custom_log(self._apply.__name__, "selector {mac: %s}" % m[1])

        self.custom_log(
            self._apply.__name__,
            "finished with "
            "[self._done_etcd_member: %s] "
            "[self._done_control_plane: %s] "
            "[self.etcd_initial_cluster %s] "
            "[self.etcd_initial_cluster_set %s]" % (
                len(self._done_etcd_member), len(self._done),
                len(self.etcd_initial_cluster), len(self.etcd_initial_cluster_set)))

    @property
    def k8s_endpoint(self):
        e = ["http://%s:%d" % (k[0], self.api_server_port) for k in self._done]
        random.shuffle(e)
        return e

    @property
    def ip_list(self):
        return [k[0] for k in self._done_etcd_member]

    @property
    def done_list(self):
        return [k for k in self._done_etcd_member]

    @property
    def wide_done_list(self):
        return self.done_list

    def apply(self):
        self.custom_log(self.apply.__name__, "begin")
        # Etcd Members + Kubernetes Control Plane
        if len(self._done_etcd_member) < self.etcd_members_nb:
            self.custom_log(self.apply.__name__, "len(self._done_etcd_member) < self.etcd_members_nb | %d < %d" %
                            (len(self._done_etcd_member), self.etcd_members_nb))
            discovery = self.fetch_discovery(self.api_endpoint)
            self._fifo_members_simple(discovery)
            if len(self._pending_etcd_member) == self.etcd_members_nb:
                self._apply()

        else:
            self.custom_log(self.apply.__name__, "already complete")
            return True

        if len(self._done_etcd_member) < self.etcd_members_nb:
            return False
        else:
            self.custom_log(self.apply.__name__, "complete")
            return True


class EtcdMemberScheduler(EtcdMemberK8sControlPlaneScheduler):
    __name__ = "EtcdMemberScheduler"

    def __init__(self,
                 api_endpoint, bootcfg_path,
                 ignition_member,
                 bootcfg_prefix="",
                 extra_selectors=None):
        self.log.debug("instancing %s" % self.__name__)
        self.api_endpoint = api_endpoint
        self.bootcfg_path = bootcfg_path
        self.bootcfg_prefix = bootcfg_prefix
        self._extra_selectors = self.get_extra_selectors(extra_selectors)

        # Etcd member area
        self._ignition_member = ignition_member
        self._pending_etcd_member = set()
        self._done_etcd_member = set()

    def _apply(self):
        self.custom_log(self._apply.__name__, "in progress...")

        marker = "%s%smember" % (self.bootcfg_prefix, "e")  # e for Etcd

        if self.etcd_initial_cluster_set:
            self.custom_log(
                self._apply.__name__, "self.etcd_initial_cluster_set is not empty", level="error")
            raise AttributeError("self.etcd_initial_cluster_set is not empty: %s" % self.etcd_initial_cluster_set)

        for i, m in enumerate(self._pending_etcd_member):
            self.etcd_initial_cluster_set.add("%s%d=http://%s:2380" % (self.etcd_name, i, m[0]))

        for i, m in enumerate(self._pending_etcd_member):
            # m = (IPv4, MAC, CIDRv4, Gateway)
            s = {"mac": m[1]}
            hostname = self.get_dns_name(m[0], "etcd-member-%d" % i)
            s.update(self._extra_selectors)
            gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_member,
                bootcfg_path=self.bootcfg_path,
                selector=s,
                extra_metadata={
                    "etcd_name": "%s%d" % (self.etcd_name, i),
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_initial_advertise_peer_urls": "http://%s:2380" % m[0],
                    "etcd_advertise_client_urls": "http://%s:2379" % m[0],
                    "hostname": hostname,
                    "cni": json.dumps(self.cni_ipam(m[2], m[3]))
                }
            )
            gen.dumps()
            self._done_etcd_member.add(m)
            self.custom_log(self._apply.__name__, "selector {mac: %s}" % m[1])

        self.custom_log(
            self._apply.__name__,
            "finished with "
            "[self._done_etcd_member: %s] "
            "[self.etcd_initial_cluster %s] "
            "[self.etcd_initial_cluster_set %s]" % (
                len(self._done_etcd_member),
                len(self.etcd_initial_cluster), len(self.etcd_initial_cluster_set)))
