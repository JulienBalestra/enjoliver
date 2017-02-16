import json
import os
import random
import re
import socket

import ipaddr
import requests

import generator
import logger
import schedulerv2
from configs import EnjoliverConfig

ec = EnjoliverConfig()


class ConfigSyncSchedules(object):
    __name__ = "ConfigSyncSchedules"

    log = logger.get_logger(__file__)

    sub_ips = ec.sub_ips
    range_nb_ips = ec.range_nb_ips
    skip_ips = ec.skip_ips

    def __init__(self, api_uri, matchbox_path, ignition_dict, extra_selector_dict=None):
        """
        :param api_uri: http://1.1.1.1:5000
        :param matchbox_path: /var/lib/matchbox
        :param ignition_dict: ignition.yaml
        """
        self.api_uri = api_uri
        os.environ["API_URI"] = self.api_uri
        self.matchbox_path = matchbox_path
        self.ignition_dict = ignition_dict
        self._ensure_ignition_are_here()
        self.extra_selector = extra_selector_dict if extra_selector_dict else {}

    def _ensure_ignition_are_here(self):
        for k, v in self.ignition_dict.iteritems():
            f = "%s/ignition/%s.yaml" % (self.matchbox_path, v)
            if os.path.isfile(f) is False:
                self.log.error("%s:%s -> %s is not here" % (k, v, f))
                raise IOError(f)

            self.log.info("%s:%s -> %s is here" % (k, v, f))

    def get_dns_name(self, host_ipv4, default=""):
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
            self.log.warning("fail to get host by addr %s returning %s" % (host_ipv4, default))
            return default

        except Exception as e:
            self.log.error("fail to get host by addr: %s %s" % (e, e.message))
            raise

    def get_dns_attr(self, fqdn):
        """
        TODO: Use LLDP to avoid vendor specific usage
        :param fqdn: e.g: r13-srv3.dc-1.foo.bar.cr
        :return:
        """
        d = {
            "shortname": "",
            "dc": "",
            "domain": "",
            "rack": "",
            "pos": "",
        }
        s = fqdn.split(".")
        d["shortname"] = s[0]
        try:
            d["dc"] = s[1]
        except IndexError:
            self.log.error("IndexError %s[1] after split(.)" % fqdn)
            return d
        d["domain"] = ".".join(s[1:])
        try:
            rack, pos = s[0].split("-")
            d["rack"] = re.sub("[^0-9]+", "", rack)
            d["pos"] = re.sub("[^0-9]+", "", pos)
        except ValueError:
            self.log.error("error during the split rack/pos %s" % s[0])
        return d

    @staticmethod
    def cni_ipam(host_cidrv4, host_gateway):
        """
        With the class variables provide a way to generate a static host-local ipam
        :param host_cidrv4:
        :param host_gateway:
        :return: dict
        """
        host = ipaddr.IPNetwork(host_cidrv4)
        subnet = host
        ip_cut = int(host.ip.__str__().split(".")[-1])
        if ConfigSyncSchedules.sub_ips:
            sub = ipaddr.IPNetwork(host.network).ip + (ip_cut * ConfigSyncSchedules.sub_ips)
            host = ipaddr.IPNetwork(sub)
        range_start = host.ip + ConfigSyncSchedules.skip_ips
        range_end = range_start + ConfigSyncSchedules.range_nb_ips
        ipam = {
            "type": "host-local",
            "subnet": "%s/%s" % (subnet.network.__str__(), subnet.prefixlen),
            "rangeStart": range_start.__str__(),
            "rangeEnd": range_end.__str__(),
            "gateway": host_gateway,
            "routes": [{"dst": "0.0.0.0/0"}]
        }
        return ipam

    def get_extra_selectors(self, extra_selectors):
        """
        Extra selectors are passed to Matchbox
        :param extra_selectors: dict
        :return:
        """
        if extra_selectors:
            if type(extra_selectors) is dict:
                self.log.debug("extra selectors: %s" % extra_selectors)
                return extra_selectors

            self.log.error("invalid extra selectors: %s" % extra_selectors)
            raise TypeError("%s %s is not type dict" % (extra_selectors, type(extra_selectors)))

        self.log.debug("no extra selectors")
        return {}

    @property
    def etcd_member_ip_list(self):
        return self._query_ip_list(schedulerv2.ScheduleRoles.etcd_member)

    @property
    def kubernetes_control_plane_ip_list(self):
        return self._query_ip_list(schedulerv2.ScheduleRoles.kubernetes_control_plane)

    @property
    def kubernetes_nodes_ip_list(self):
        return self._query_ip_list(schedulerv2.ScheduleRoles.kubernetes_node)

    @property
    def etcd_initial_cluster(self):
        ips = self.etcd_member_ip_list
        e = ["%s=http://%s:%d" % (k, k, ec.etcd_initial_advertise_peer_port) for k in ips]
        random.shuffle(e)
        return ",".join(e)

    @property
    def etcd_member_client_uri_list(self):
        ips = self.etcd_member_ip_list
        e = ["http://%s:%d" % (k, ec.etcd_advertise_client_port) for k in ips]
        random.shuffle(e)
        return e

    @property
    def etcd_member_peer_uri_list(self):
        ips = self.etcd_member_ip_list
        e = ["http://%s:%d" % (k, ec.etcd_initial_advertise_peer_port) for k in ips]
        random.shuffle(e)
        return e

    @property
    def kubernetes_control_plane(self):
        ips = self.kubernetes_control_plane_ip_list
        k8s = ["http://%s:%d" % (k8s, ec.kubernetes_api_server_port) for k8s in ips]
        random.shuffle(k8s)
        return ",".join(k8s)

    def etcd_member_kubernetes_control_plane(self):
        marker = self.etcd_member_kubernetes_control_plane.__name__
        roles = schedulerv2.EtcdMemberKubernetesControlPlane.roles

        machine_roles = self._query_roles(*roles)
        for i, m in enumerate(machine_roles):
            automatic_name = "k8s-control-plane-%d" % i
            selector = {"mac": m["mac"]}
            fqdn = self.get_dns_name(m["ipv4"], automatic_name)
            dns_attr = self.get_dns_attr(fqdn)
            selector.update(self.get_extra_selectors(self.extra_selector))
            gen = generator.Generator(
                api_uri=self.api_uri,
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self.ignition_dict[marker],
                matchbox_path=self.matchbox_path,
                selector=selector,
                extra_metadata={
                    # Etcd
                    "etcd_name": m["ipv4"],
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_initial_advertise_peer_urls": "http://%s:%d" % (
                        m["ipv4"], ec.etcd_initial_advertise_peer_port),
                    "etcd_advertise_client_urls": "http://%s:%d" % (
                        m["ipv4"], ec.etcd_advertise_client_port),
                    "etcd_member_client_uri_list": ",".join(self.etcd_member_client_uri_list),
                    "etcd_member_peer_uri_list": ",".join(self.etcd_member_peer_uri_list),
                    "etcd_data_dir": ec.etcd_data_dir,
                    # K8s Control Plane
                    "kubelet_ip": "%s" % m["ipv4"],
                    "kubelet_name": "%s" % m["ipv4"] if fqdn == automatic_name else fqdn,
                    "k8s_apiserver_count": len(machine_roles),
                    "k8s_advertise_ip": "%s" % m["ipv4"],
                    "k8s_image_url": ec.k8s_image_url,
                    "k8s_service_cluster_ip_range": ec.kubernetes_service_cluster_ip_range,
                    # IPAM
                    "cni": json.dumps(self.cni_ipam(m["cidrv4"], m["gateway"])),
                    "network": {
                        "cidrv4": m["cidrv4"],
                        "gateway": m["gateway"],
                        "ip": m["ipv4"],
                    },
                    # host
                    "hostname": dns_attr["shortname"],
                    "dns_attr": dns_attr,
                }
            )
            gen.dumps()

    def kubernetes_nodes(self):
        marker = self.kubernetes_nodes.__name__
        roles = schedulerv2.KubernetesNode.roles

        machine_roles = self._query_roles(*roles)
        for i, m in enumerate(machine_roles):
            automatic_name = "k8s-node-%d" % i
            selector = {"mac": m["mac"]}
            fqdn = self.get_dns_name(m["ipv4"], automatic_name)
            dns_attr = self.get_dns_attr(fqdn)
            selector.update(self.get_extra_selectors(self.extra_selector))
            gen = generator.Generator(
                api_uri=self.api_uri,
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name=marker,
                ignition_id="%s.yaml" % self.ignition_dict[marker],
                matchbox_path=self.matchbox_path,
                selector=selector,
                extra_metadata={
                    # Etcd
                    "etcd_initial_cluster": self.etcd_initial_cluster,
                    "etcd_advertise_client_urls": "http://%s:%d" % (
                        m["ipv4"], ec.etcd_advertise_client_port),
                    "etcd_member_client_uri_list": ",".join(self.etcd_member_client_uri_list),
                    "etcd_member_peer_uri_list": ",".join(self.etcd_member_peer_uri_list),
                    "etcd_proxy": "on",
                    "etcd_data_dir": ec.etcd_data_dir,
                    # Kubelet
                    "kubelet_ip": "%s" % m["ipv4"],
                    "kubelet_name": "%s" % m["ipv4"] if fqdn == automatic_name else fqdn,
                    "k8s_endpoint": self.kubernetes_control_plane,
                    "k8s_image_url": ec.k8s_image_url,
                    "k8s_service_cluster_ip_range": ec.kubernetes_service_cluster_ip_range,
                    # IPAM
                    "cni": json.dumps(self.cni_ipam(m["cidrv4"], m["gateway"])),
                    "network": {
                        "cidrv4": m["cidrv4"],
                        "gateway": m["gateway"],
                        "ip": m["ipv4"],
                    },
                    # host
                    "hostname": dns_attr["shortname"],
                    "dns_attr": dns_attr,
                }
            )
            gen.dumps()

    def apply(self):
        self.etcd_member_kubernetes_control_plane()
        self.kubernetes_nodes()

    def _query_roles(self, *roles):
        roles = "&".join(roles)
        self.log.debug("%s roles='%s'" % (self._query_roles.__name__, roles))
        r = requests.get("%s/scheduler/%s" % (self.api_uri, roles))
        d = json.loads(r.content)
        r.close()
        return d

    def _query_ip_list(self, role):
        self.log.debug("%s role='%s'" % (self._query_ip_list.__name__, role))
        r = requests.get("%s/scheduler/ip-list/%s" % (self.api_uri, role))
        d = json.loads(r.content)
        r.close()
        return d
