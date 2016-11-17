import abc
import json
import os
import time
import urllib2

import generator


class CommonScheduler(object):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def get_machine_boot_ip_mac(discovery):
        mac = discovery["boot-info"]["mac"]
        ipv4 = None
        for i in discovery["interfaces"]:
            if i["MAC"] == mac:
                ipv4 = i["IPv4"]
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
        done = self._etcd_member_instance.ip_list + list(self._done_etcd_proxy)
        if len(self._pending_etcd_proxy) != 0:
            raise AssertionError("len(self._pending_etcd_proxy) != 0 -> %s" % str(self._pending_etcd_proxy))

        if len(discovery) > len(done):
            for machine in discovery:
                ip_mac = self.get_machine_boot_ip_mac(machine)
                if ip_mac in self._etcd_member_instance.done_list:
                    os.write(2, "\r-> Skip because Etcd Member %s\n\r" % str(ip_mac))
                elif ip_mac in self._done_etcd_proxy:
                    os.write(2, "\r-> Skip because Etcd Proxy %s\n\r" % str(ip_mac))
                else:
                    os.write(2, "\r-> Pending Etcd Proxy %s\n\r" % str(ip_mac))
                    self._pending_etcd_proxy.add(ip_mac)
        else:
            os.write(2, "\r-> no machine 0 %s\n\r" % len(self._pending_etcd_proxy))

    def _apply_proxy(self):
        os.write(2, "\r-> %s.%s in progress...\n\r" % (self.__name__, self._apply_proxy.__name__))

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
            os.write(2, "\r-> %s.%s selector {mac: %s}\n\r" % (
                self.__name__, self._apply_proxy.__name__, nic))

        if self._pending_etcd_proxy - self._done_etcd_proxy:
            raise AssertionError("self._pending_etcd_proxy - self._done_etcd_proxy have to return an empty set")
        self._pending_etcd_proxy = new_pending

    def apply(self):
        self.apply_member()
        discovery = self.fetch_discovery(self.api_endpoint)
        self._fall_back_to_proxy(discovery)
        if len(self._pending_etcd_proxy) > 0:
            self._apply_proxy()

        os.write(2, "\r-> %s.%s total %d\n\r" % (
            self.__name__,
            self.apply.__name__,
            len(self._done_etcd_proxy)))
        return len(self._done_etcd_proxy)

    @property
    def ip_list(self):
        return [k[0] for k in self._done_etcd_proxy]

    @property
    def done_list(self):
        return [k for k in self._done_etcd_proxy]


class K8sControlPlaneScheduler(CommonScheduler):
    __name__ = "K8sControlPlaneScheduler"

    apply_deps_delay = 6
    apply_deps_tries = apply_deps_delay * 50

    control_plane_nb = 3

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
            os.write(2, "\r-> no machine 0/%d\n\r" % self.control_plane_nb)
            return self._pending_control_plane

        elif len(discovery) < self.control_plane_nb:
            os.write(2, "\r-> not enough machines %d/%d\n\r" % (
                len(discovery), self.control_plane_nb))
            return self._pending_control_plane

        else:
            for machine in discovery:
                ip_mac = self.get_machine_boot_ip_mac(machine)

                if ip_mac in self._etcd_member_instance.done_list:
                    os.write(2, "\r-> Skip because Etcd Member %s\n\r" % str(ip_mac))
                elif ip_mac in self._done_control_plane:
                    os.write(2, "\r-> Skip because K8s Control Plane -> WARNING %s\n\r" % str(ip_mac))
                elif len(self._pending_control_plane) < self.control_plane_nb:
                    os.write(2, "\r-> Pending K8s Control Plane %s\n\r" % str(ip_mac))
                    self._pending_control_plane.add(ip_mac)
                else:
                    break

        os.write(2, "\r-> enough machines %d/%d\n\r" % (len(discovery), self.control_plane_nb))
        return self._pending_control_plane

    def _apply_control_plane(self):
        os.write(2, "\r-> %s.%s in progress...\n\r" % (self.__name__, self._apply_control_plane.__name__))

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
                    "apiserver-count": self.control_plane_nb
                }
            )
            self._gen.dumps()
            self._done_control_plane.add(nic)
            new_pending = self._pending_control_plane - self._done_control_plane
            os.write(2, "\r-> %s.%s selector {mac: %s}\n\r" % (
                self.__name__, self._apply_control_plane.__name__, nic))

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
            os.write(2, "\r-> %s.%s already complete\n\r" %
                     (self.__name__, self.apply.__name__))
            return True

        if len(self._done_control_plane) < self.control_plane_nb:
            return False
        else:
            os.write(2, "\r-> %s.%s complete\n\r" %
                     (self.__name__, self.apply.__name__))
            return True

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
            os.write(2, "\r-> no machine 0/%d\n\r" % self.etcd_members_nb)
            return self._pending_etcd_member

        elif len(discovery) < self.etcd_members_nb:
            os.write(2, "\r-> not enough machines %d/%d\n\r" % (
                len(discovery), self.etcd_members_nb))
            return self._pending_etcd_member

        else:
            for machine in discovery:
                ip_mac = self.get_machine_boot_ip_mac(machine)
                if len(self._pending_etcd_member) < self.etcd_members_nb:
                    self._pending_etcd_member.add(ip_mac)
                else:
                    break

        os.write(2, "\r-> enough machines %d/%d\n\r" % (len(discovery), self.etcd_members_nb))
        return self._pending_etcd_member

    def _apply_member(self):
        os.write(2, "\r-> %s.%s in progress...\n\r" % (self.__name__, self._apply_member.__name__))

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
            os.write(2, "\r-> %s.%s selector {mac: %s}\n\r" % (
                self.__name__, self._apply_member.__name__, nic))
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

    def apply(self):
        # Etcd Members
        if len(self._done_etcd_member) < self.etcd_members_nb:
            discovery = self.fetch_discovery(self.api_endpoint)
            self._fifo_members_simple(discovery)
            if len(self._pending_etcd_member) == self.etcd_members_nb:
                self._apply_member()

        else:
            os.write(2, "\r-> %s.%s already complete\n\r" %
                     (self.__name__, self.apply.__name__))
            return True

        if len(self._done_etcd_member) < self.etcd_members_nb:
            return False
        else:
            os.write(2, "\r-> %s.%s complete\n\r" %
                     (self.__name__, self.apply.__name__))
            return True
