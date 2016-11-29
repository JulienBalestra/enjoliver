import abc
import json
import os
import time
import urllib2

import sys

import generator


class CommonScheduler(object):
    __metaclass__ = abc.ABCMeta

    def log(self, func_name, message):
        os.write(1, "\r%s.%s %s\n\r" % (self.__name__, func_name, message))
        sys.stdout.flush()

    @staticmethod
    def get_machine_boot_ip_mac(discovery):
        mac = discovery["boot-info"]["mac"]
        ipv4 = None
        for i in discovery["interfaces"]:
            if i["mac"] == mac:
                ipv4 = i["ipv4"]
        if ipv4 is None:
            raise LookupError("%s Lookup failed in %s" % (mac, discovery))
        return ipv4, mac

    @staticmethod
    def fetch_discovery(api_endpoint):
        os.write(2, "\r-> fetch %s\n\r" % api_endpoint)
        content = urllib2.urlopen("%s/discovery" % api_endpoint)
        response_body = content.read()
        content.close()
        interfaces = json.loads(response_body)
        os.write(2, "\r-> fetch done\n\r")
        return interfaces

    @abc.abstractmethod
    def apply(self):
        return

    @abc.abstractproperty
    def etcd_initial_cluster(self):
        pass

    @abc.abstractproperty
    def ip_list(self):
        pass

    @abc.abstractproperty
    def done_list(self):
        pass

    @abc.abstractproperty
    def wide_done_list(self):
        pass


class EtcdProxyScheduler(CommonScheduler):
    __name__ = "EtcdProxyScheduler"
    apply_deps_delay = 6
    apply_deps_tries = apply_deps_delay * 50

    def __init__(self,
                 etcd_member_instance,
                 ignition_proxy,
                 apply_first=False):

        self._etcd_initial_cluster = None
        self._etcd_member_instance = etcd_member_instance

        if isinstance(self._etcd_member_instance, EtcdMemberScheduler) is False:
            raise AttributeError("%s not a instanceof(%s)" % (
                "etcd_member_instance", EtcdMemberScheduler.__name__))

        if apply_first is True:
            self.apply_member()

        self._ignition_proxy = ignition_proxy
        self.api_endpoint = self._etcd_member_instance.api_endpoint
        self.bootcfg_prefix = self._etcd_member_instance.bootcfg_prefix
        self.bootcfg_path = self._etcd_member_instance.bootcfg_path
        self._gen = generator.Generator
        self._done_etcd_proxy = set()
        self._pending_etcd_proxy = set()

    @property
    def etcd_initial_cluster(self):
        if self._etcd_initial_cluster is None:
            self._etcd_initial_cluster = self._etcd_member_instance.etcd_initial_cluster
        return self._etcd_initial_cluster

    def apply_member(self):
        if self.etcd_initial_cluster is not None:
            return True
        for t in xrange(self.apply_deps_tries):
            if self._etcd_member_instance.apply() is True:
                self._etcd_initial_cluster = self._etcd_member_instance.etcd_initial_cluster
                return True
            time.sleep(self.apply_deps_delay)
        raise RuntimeError("timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries))

    def _fall_back_to_proxy(self, discovery):
        if len(self._pending_etcd_proxy) != 0:
            raise AssertionError("len(self._pending_etcd_proxy) != 0 -> %s" % str(self._pending_etcd_proxy))

        if len(discovery) > len(self.wide_done_list):
            for machine in discovery:
                ip_mac = self.get_machine_boot_ip_mac(machine)
                if ip_mac in self.done_list:
                    self.log(self._fall_back_to_proxy.__name__,
                             "Skip because Etcd Proxy %s" % str(ip_mac))
                elif ip_mac in self.wide_done_list:
                    self.log(self._fall_back_to_proxy.__name__,
                             "Skip because Wide Schedule %s" % str(ip_mac))
                else:
                    self.log(self._fall_back_to_proxy.__name__,
                             "Pending Etcd Proxy %s" % str(ip_mac))
                    self._pending_etcd_proxy.add(ip_mac)
        else:
            self.log(self._fall_back_to_proxy.__name__,
                     "no machine 0 %s" % len(self._pending_etcd_proxy))

    def _apply_proxy(self):
        self.log(self._apply_proxy.__name__, "in progress...")

        marker = "%s%sproxy" % (self.bootcfg_prefix, "e")  # e for Etcd

        base = len(self._done_etcd_proxy)
        new_pending = set()
        for i, nic in enumerate(self._pending_etcd_proxy):
            # nic = (IPv4, MAC)
            i += base
            self._gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_proxy,
                bootcfg_path=self.bootcfg_path,
                selector={"mac": nic[1]},
                extra_metadata={
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_advertise_client_urls": "http://%s:2379" % nic[0],
                    "etcd_proxy": "on"
                }
            )
            self._gen.dumps()
            self._done_etcd_proxy.add(nic)
            new_pending = self._pending_etcd_proxy - self._done_etcd_proxy
            self.log(self._apply_proxy.__name__, "selector {mac: %s}" % nic[1])

        if self._pending_etcd_proxy - self._done_etcd_proxy:
            raise AssertionError("self._pending_etcd_proxy - self._done_etcd_proxy have to return an empty set")
        self._pending_etcd_proxy = new_pending

    def apply(self):
        self.apply_member()
        discovery = self.fetch_discovery(self.api_endpoint)
        self._fall_back_to_proxy(discovery)
        if len(self._pending_etcd_proxy) > 0:
            self._apply_proxy()

        self.log(self.apply.__name__, " total %d" % len(self._done_etcd_proxy))
        return len(self._done_etcd_proxy)

    @property
    def ip_list(self):
        return [k[0] for k in self._done_etcd_proxy]

    @property
    def done_list(self):
        return [k for k in self._done_etcd_proxy]

    @property
    def wide_done_list(self):
        return self.done_list + self._etcd_member_instance.wide_done_list


class K8sNodeScheduler(CommonScheduler):
    __name__ = "K8sNodeScheduler"
    apply_deps_delay = 6
    apply_deps_tries = apply_deps_delay * 50

    def __init__(self,
                 k8s_control_plane,
                 ignition_node,
                 apply_first=False):

        self._etcd_initial_cluster = None
        self._k8s_control_plane_instance = k8s_control_plane

        if isinstance(self._k8s_control_plane_instance, K8sControlPlaneScheduler) is False:
            raise AttributeError("%s not a instanceof(%s)" % (
                "k8s_control_plane", K8sControlPlaneScheduler.__name__))

        if apply_first is True:
            self.apply_control_plane()

        self._ignition_node = ignition_node
        self.api_endpoint = self._k8s_control_plane_instance.api_endpoint
        self.bootcfg_prefix = self._k8s_control_plane_instance.bootcfg_prefix
        self.bootcfg_path = self._k8s_control_plane_instance.bootcfg_path
        self._gen = generator.Generator
        self._done_k8s_node = set()
        self._pending_k8s_node = set()

    @property
    def etcd_initial_cluster(self):
        if self._etcd_initial_cluster is None:
            self._etcd_initial_cluster = self._k8s_control_plane_instance.etcd_initial_cluster
        return self._etcd_initial_cluster

    def apply_control_plane(self):
        if len(self._k8s_control_plane_instance.done_list) > 0:
            return True
        for t in xrange(self.apply_deps_tries):
            if self._k8s_control_plane_instance.apply() is True:
                self._etcd_initial_cluster = self._k8s_control_plane_instance.etcd_initial_cluster
                return True
            time.sleep(self.apply_deps_delay)
        raise RuntimeError("timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries))

    def _fall_back_to_node(self, discovery):
        if len(self._pending_k8s_node) != 0:
            raise AssertionError("len(self._pending_k8s_node) != 0 -> %s" % str(self._pending_k8s_node))

        if len(discovery) > len(self.wide_done_list):
            for machine in discovery:
                ip_mac = self.get_machine_boot_ip_mac(machine)
                if ip_mac in self._done_k8s_node:
                    self.log(self._fall_back_to_node.__name__,
                             "Skip because K8s Node %s" % str(ip_mac))
                elif ip_mac in self.wide_done_list:
                    self.log(self._fall_back_to_node.__name__,
                             "Skip because in Wide Schedule %s" % str(ip_mac))
                else:
                    self.log(self._fall_back_to_node.__name__,
                             "Pending K8s Node %s" % str(ip_mac))
                    self._pending_k8s_node.add(ip_mac)
        else:
            self.log(self._fall_back_to_node.__name__,
                     "no machine 0 %s" % len(self._pending_k8s_node))

    def _apply_k8s_node(self):
        self.log(self._apply_k8s_node.__name__, "in progress...")

        marker = "%s%snode" % (self.bootcfg_prefix, "k8s")

        base = len(self._done_k8s_node)
        new_pending = set()
        for i, nic in enumerate(self._pending_k8s_node):
            # nic = (IPv4, MAC)
            i += base
            self._gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_node,
                bootcfg_path=self.bootcfg_path,
                selector={"mac": nic[1]},
                extra_metadata={
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_advertise_client_urls": "http://%s:2379" % nic[0],
                    "etcd_proxy": "on",
                    "k8s_advertise_ip": "%s" % nic[0],
                    "k8s_endpoint": ",".join(self._k8s_control_plane_instance.k8s_endpoint)
                }
            )
            self._gen.dumps()
            self._done_k8s_node.add(nic)
            new_pending = self._pending_k8s_node - self._done_k8s_node
            self.log(self._apply_k8s_node.__name__, "selector {mac: %s}" % nic[1])

        if self._pending_k8s_node - self._done_k8s_node:
            raise AssertionError("self._pending_k8s_node - self._done_k8s_node have to return an empty set")
        self._pending_k8s_node = new_pending

    def apply(self):
        self.apply_control_plane()
        discovery = self.fetch_discovery(self.api_endpoint)
        self._fall_back_to_node(discovery)
        if len(self._pending_k8s_node) > 0:
            self._apply_k8s_node()

        self.log(self.apply.__name__, "total %d" % len(self._done_k8s_node))
        return len(self._done_k8s_node)

    @property
    def ip_list(self):
        return [k[0] for k in self._done_k8s_node]

    @property
    def done_list(self):
        return [k for k in self._done_k8s_node]

    @property
    def wide_done_list(self):
        return self.done_list + self._k8s_control_plane_instance.wide_done_list


class K8sControlPlaneScheduler(CommonScheduler):
    __name__ = "K8sControlPlaneScheduler"

    apply_deps_delay = 6
    apply_deps_tries = apply_deps_delay * 50

    control_plane_nb = 3
    api_server_port = 8080

    def __init__(self,
                 etcd_member_instance,
                 ignition_control_plane,
                 apply_first=False):

        self._etcd_initial_cluster = None
        self._etcd_member_instance = etcd_member_instance

        if isinstance(self._etcd_member_instance, EtcdMemberScheduler) is False:
            raise AttributeError("%s not a instanceof(%s)" % (
                "etcd_member_instance", EtcdMemberScheduler.__name__))

        if apply_first is True:
            self.apply_member()

        self._ignition_control_plane = ignition_control_plane
        self.api_endpoint = self._etcd_member_instance.api_endpoint
        self.bootcfg_prefix = self._etcd_member_instance.bootcfg_prefix
        self.bootcfg_path = self._etcd_member_instance.bootcfg_path
        self._gen = generator.Generator
        self._done_control_plane = set()
        self._pending_control_plane = set()

    def apply_member(self):
        if self.etcd_initial_cluster is not None:
            return True
        for t in xrange(self.apply_deps_tries):
            if self._etcd_member_instance.apply() is True:
                self._etcd_initial_cluster = self._etcd_member_instance.etcd_initial_cluster
                return True
            time.sleep(self.apply_deps_delay)
        raise RuntimeError("timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries))

    def _fifo_control_plane_simple(self, discovery):
        if not discovery or len(discovery) == 0:
            self.log(self._fifo_control_plane_simple.__name__,
                     "no machine 0/%d" % self.control_plane_nb)
            return self._pending_control_plane

        elif len(discovery) < self.control_plane_nb:
            self.log(self._fifo_control_plane_simple.__name__,
                     "not enough machines %d/%d" % (
                         len(discovery), self.control_plane_nb))
            return self._pending_control_plane

        else:
            for machine in discovery:
                ip_mac = self.get_machine_boot_ip_mac(machine)
                if ip_mac in self._done_control_plane:
                    self.log(self._fifo_control_plane_simple.__name__,
                             "WARNING Skip because K8s Control Plane  %s" % str(ip_mac))
                elif ip_mac in self.wide_done_list:
                    self.log(self._fifo_control_plane_simple.__name__,
                             "Skip because Wide Schedule %s" % str(ip_mac))
                elif len(self._pending_control_plane) < self.control_plane_nb:
                    self.log(self._fifo_control_plane_simple.__name__,
                             "Pending K8s Control Plane %s" % str(ip_mac))
                    self._pending_control_plane.add(ip_mac)
                else:
                    break

        self.log(self._fifo_control_plane_simple.__name__,
                 "enough machines %d/%d" % (len(discovery), self.control_plane_nb))
        return self._pending_control_plane

    def _apply_control_plane(self):
        self.log(self._apply_control_plane.__name__, "in progress...")

        marker = "%s%scontrol-plane" % (self.bootcfg_prefix, "k8s")  # e for Etcd

        new_pending = set()
        for i, nic in enumerate(self._pending_control_plane):
            # nic = (IPv4, MAC)
            self._gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_control_plane,
                bootcfg_path=self.bootcfg_path,
                selector={"mac": nic[1]},
                extra_metadata={
                    # Etcd Proxy
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_advertise_client_urls": "http://%s:2379" % nic[0],
                    "etcd_proxy": "on",
                    # K8s Control Plane
                    "k8s_apiserver_count": self.control_plane_nb,
                    "k8s_advertise_ip": "%s" % nic[0],
                }
            )
            self._gen.dumps()
            self._done_control_plane.add(nic)
            new_pending = self._pending_control_plane - self._done_control_plane
            self.log(self._apply_control_plane.__name__, "selector {mac: %s}" % nic[1])

        if self._pending_control_plane - self._done_control_plane:
            raise AssertionError("self._apply_control_plane - self._done_control_plane have to return an empty set")
        self._pending_control_plane = new_pending

    def apply(self):
        self.apply_member()
        # K8s Control Plane
        if len(self._done_control_plane) < self.control_plane_nb:
            discovery = self.fetch_discovery(self.api_endpoint)
            self._fifo_control_plane_simple(discovery)
            if len(self._pending_control_plane) == self.control_plane_nb:
                self._apply_control_plane()

        else:
            self.log(self.apply.__name__, "already complete")
            return True

        if len(self._done_control_plane) < self.control_plane_nb:
            return False
        else:
            self.log(self.apply.__name__, "complete")
            return True

    @property
    def k8s_endpoint(self):
        return ["http://%s:%d" % (k[0], self.api_server_port) for k in self._done_control_plane]

    @property
    def etcd_initial_cluster(self):
        if self._etcd_initial_cluster is None:
            self._etcd_initial_cluster = self._etcd_member_instance.etcd_initial_cluster
        return self._etcd_initial_cluster

    @property
    def ip_list(self):
        return [k[0] for k in self._done_control_plane]

    @property
    def done_list(self):
        return [k for k in self._done_control_plane]

    @property
    def wide_done_list(self):
        return self.done_list + self._etcd_member_instance.wide_done_list


class EtcdMemberScheduler(CommonScheduler):
    etcd_members_nb = 3
    __name__ = "EtcdMemberScheduler"
    etcd_name = "static"  # basename

    def __init__(self,
                 api_endpoint, bootcfg_path,
                 ignition_member,
                 bootcfg_prefix=""):

        self.api_endpoint = api_endpoint
        self._gen = generator.Generator
        self.bootcfg_path = bootcfg_path
        self.bootcfg_prefix = bootcfg_prefix

        # Etcd member area
        self._ignition_member = ignition_member
        self._pending_etcd_member = set()
        self._done_etcd_member = set()
        self._etcd_initial_cluster = None

    def _fifo_members_simple(self, discovery):

        if not discovery or len(discovery) == 0:
            self.log(self._fifo_members_simple.__name__, "no machine 0/%d" % self.etcd_members_nb)
            return self._pending_etcd_member

        elif len(discovery) < self.etcd_members_nb:
            self.log(self._fifo_members_simple.__name__,
                     "not enough machines %d/%d" % (len(discovery), self.etcd_members_nb))
            return self._pending_etcd_member

        else:
            for machine in discovery:
                ip_mac = self.get_machine_boot_ip_mac(machine)
                if len(self._pending_etcd_member) < self.etcd_members_nb:
                    self._pending_etcd_member.add(ip_mac)
                else:
                    break

        self.log(self._fifo_members_simple.__name__,
                 "enough machines %d/%d" % (len(discovery), self.etcd_members_nb))
        return self._pending_etcd_member

    def _apply_member(self):
        self.log(self._apply_member.__name__, "in progress...")

        marker = "%s%smember" % (self.bootcfg_prefix, "e")  # e for Etcd

        etcd_initial_cluster_list = []
        for i, m in enumerate(self._pending_etcd_member):
            etcd_initial_cluster_list.append("%s%d=http://%s:2380" % (self.etcd_name, i, m[0]))

        etcd_initial_cluster = ",".join(etcd_initial_cluster_list)

        for i, nic in enumerate(self._pending_etcd_member):
            # nic = (IPv4, MAC)
            self._gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self._ignition_member,
                bootcfg_path=self.bootcfg_path,
                selector={"mac": nic[1]},
                extra_metadata={
                    "etcd_name": "%s%d" % (self.etcd_name, i),
                    "etcd_initial_cluster": etcd_initial_cluster,
                    "etcd_initial_advertise_peer_urls": "http://%s:2380" % nic[0],
                    "etcd_advertise_client_urls": "http://%s:2379" % nic[0],

                }
            )
            self._gen.dumps()
            self._done_etcd_member.add(nic)
            self.log(self._apply_member.__name__, "selector {mac: %s}" % nic[1])
        self._etcd_initial_cluster = etcd_initial_cluster

    @property
    def etcd_initial_cluster(self):
        return self._etcd_initial_cluster

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
        # Etcd Members
        if len(self._done_etcd_member) < self.etcd_members_nb:
            discovery = self.fetch_discovery(self.api_endpoint)
            self._fifo_members_simple(discovery)
            if len(self._pending_etcd_member) == self.etcd_members_nb:
                self._apply_member()

        else:
            self.log(self.apply.__name__, "already complete")
            return True

        if len(self._done_etcd_member) < self.etcd_members_nb:
            return False
        else:
            self.log(self.apply.__name__, "complete")
            return True
