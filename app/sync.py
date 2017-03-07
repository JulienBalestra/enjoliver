import json
import os
import random
import re

import ipaddr
import requests

import generator
import logger
import schedulerv2
from configs import EnjoliverConfig

ec = EnjoliverConfig(importer=__file__)


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
        for k, v in self.ignition_dict.items():
            f = "%s/ignition/%s.yaml" % (self.matchbox_path, v)
            if os.path.isfile(f) is False:
                self.log.error("%s:%s -> %s is not here" % (k, v, f))
                raise IOError(f)

            self.log.info("%s:%s -> %s is here" % (k, v, f))

    @staticmethod
    def get_dns_attr(log, fqdn):
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
            log.error("IndexError %s[1] after split(.)" % fqdn)
            return d
        d["domain"] = ".".join(s[1:])
        try:
            rack, pos = s[0].split("-")
            d["rack"] = re.sub("[^0-9]+", "", rack)
            d["pos"] = re.sub("[^0-9]+", "", pos)
        except ValueError:
            log.error("error during the split rack/pos %s" % s[0])
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

    @staticmethod
    def shuffler_http_uri(ips, ec_value):
        ips.sort()
        e = ["http://%s:%d" % (k, ec_value) for k in ips]
        random.shuffle(e)
        return e

    @staticmethod
    def shuffler_etcd_named(ips, ec_value):
        ips.sort()
        e = ["%s=http://%s:%d" % (k, k, ec_value) for k in ips]
        random.shuffle(e)
        return ",".join(e)

    @property
    def kubernetes_etcd_initial_cluster(self):
        return self.shuffler_etcd_named(self.etcd_member_ip_list, ec.kubernetes_etcd_peer_port)

    @property
    def fleet_etcd_initial_cluster(self):
        return self.shuffler_etcd_named(self.etcd_member_ip_list, ec.fleet_etcd_peer_port)

    @property
    def kubernetes_etcd_member_client_uri_list(self):
        return self.shuffler_http_uri(self.etcd_member_ip_list, ec.kubernetes_etcd_client_port)

    @property
    def fleet_etcd_member_client_uri_list(self):
        return self.shuffler_http_uri(self.etcd_member_ip_list, ec.fleet_etcd_client_port)

    @property
    def kubernetes_etcd_member_peer_uri_list(self):
        return self.shuffler_http_uri(self.etcd_member_ip_list, ec.kubernetes_etcd_peer_port)

    @property
    def fleet_etcd_member_peer_uri_list(self):
        return self.shuffler_http_uri(self.etcd_member_ip_list, ec.fleet_etcd_peer_port)

    @property
    def kubernetes_control_plane(self):
        return self.shuffler_http_uri(self.kubernetes_control_plane_ip_list, ec.kubernetes_api_server_port)

    def produce_matchbox_data(self, marker, i, m, automatic_name, update_extra_metadata=None):
        random.seed(m["mac"].__hash__())
        fqdn = None
        try:
            fqdn = m["fqdn"]
        except KeyError as e:
            self.log.warning("%s for %s" % (e, m["mac"]))

        fqdn = automatic_name if not fqdn else fqdn

        dns_attr = self.get_dns_attr(self.log, fqdn)
        extra_metadata = {
            "etc_hosts": ec.etc_hosts,
            # Etcd
            "etcd_name": m["ipv4"],

            "kubernetes_etcd_initial_cluster": self.kubernetes_etcd_initial_cluster,
            "fleet_etcd_initial_cluster": self.fleet_etcd_initial_cluster,

            "kubernetes_etcd_initial_advertise_peer_urls": "http://%s:%d" % (
                m["ipv4"], ec.kubernetes_etcd_peer_port),
            "fleet_etcd_initial_advertise_peer_urls": "http://%s:%d" % (
                m["ipv4"], ec.fleet_etcd_peer_port),

            "kubernetes_etcd_member_client_uri_list": ",".join(self.kubernetes_etcd_member_client_uri_list),
            "fleet_etcd_member_client_uri_list": ",".join(self.fleet_etcd_member_client_uri_list),

            "kubernetes_etcd_data_dir": ec.kubernetes_etcd_data_dir,
            "fleet_etcd_data_dir": ec.fleet_etcd_data_dir,

            "kubernetes_etcd_client_port": ec.kubernetes_etcd_client_port,
            "fleet_etcd_client_port": ec.fleet_etcd_client_port,

            "kubernetes_etcd_advertise_client_urls": "http://%s:%d" % (
                m["ipv4"], ec.kubernetes_etcd_client_port),
            "fleet_etcd_advertise_client_urls": "http://%s:%d" % (
                m["ipv4"], ec.fleet_etcd_client_port),

            "fleet_etcd_servers": ec.fleet_etcd_servers,

            # Kubernetes
            "kubernetes_etcd_servers": ec.kubernetes_etcd_servers,
            "kubernetes_api_server_port": ec.kubernetes_api_server_port,
            "kubernetes_node_ip": "%s" % m["ipv4"],
            "kubernetes_node_name": "%s" % m["ipv4"] if fqdn == automatic_name else fqdn,
            "kubernetes_service_cluster_ip_range": ec.kubernetes_service_cluster_ip_range,

            "hyperkube_image_url": ec.hyperkube_image_url,
            "rkt_image_url": ec.rkt_image_url,
            "etcd_image_url": ec.etcd_image_url,
            "fleet_image_url": ec.fleet_image_url,
            "cni_image_url": ec.cni_image_url,
            # IPAM
            "cni": json.dumps(self.cni_ipam(m["cidrv4"], m["gateway"]), sort_keys=True),
            "network": {
                "cidrv4": m["cidrv4"],
                "gateway": m["gateway"],
                "ip": m["ipv4"],
            },
            # host
            "hostname": dns_attr["shortname"],
            "dns_attr": dns_attr,

        }
        selector = {"mac": m["mac"]}
        selector.update(self.get_extra_selectors(self.extra_selector))
        if update_extra_metadata:
            extra_metadata.update(update_extra_metadata)
        gen = generator.Generator(
            api_uri=self.api_uri,
            group_id="%s-%d" % (marker, i),  # one per machine
            profile_id=marker,  # link to ignition
            name=marker,
            ignition_id="%s.yaml" % self.ignition_dict[marker],
            matchbox_path=self.matchbox_path,
            selector=selector,
            extra_metadata=extra_metadata,
        )
        gen.dumps()

    def etcd_member_kubernetes_control_plane(self):
        marker = self.etcd_member_kubernetes_control_plane.__name__
        roles = schedulerv2.EtcdMemberKubernetesControlPlane.roles

        machine_roles = self._query_roles(*roles)
        for i, m in enumerate(machine_roles):
            update_md = {
                # Etcd Members
                "kubernetes_etcd_member_peer_uri_list": ",".join(self.kubernetes_etcd_member_peer_uri_list),
                "fleet_etcd_member_peer_uri_list": ",".join(self.fleet_etcd_member_peer_uri_list),

                "kubernetes_etcd_peer_port": ec.kubernetes_etcd_peer_port,
                "fleet_etcd_peer_port": ec.fleet_etcd_peer_port,

                # K8s Control Plane
                "kubernetes_apiserver_count": len(machine_roles),
                "kubernetes_advertise_ip": "%s" % m["ipv4"],  # TODO still usable ?
            }
            self.produce_matchbox_data(
                marker=marker,
                i=i,
                m=m,
                automatic_name="cp-%d-%s" % (i, m["ipv4"].replace(".", "-")),
                update_extra_metadata=update_md,
            )

    def kubernetes_nodes(self):
        marker = self.kubernetes_nodes.__name__
        roles = schedulerv2.KubernetesNode.roles

        machine_roles = self._query_roles(*roles)
        for i, m in enumerate(machine_roles):
            self.produce_matchbox_data(
                marker=marker,
                i=i,
                m=m,
                automatic_name="no-%d-%s" % (i, m["ipv4"].replace(".", "-")),
                update_extra_metadata=None,
            )

    def apply(self):
        try:
            self.etcd_member_kubernetes_control_plane()
            self.kubernetes_nodes()
        except Exception as e:
            # If the sync fail, it's not a big deal, next pass will do it again
            self.log.error("fail to apply the sync %s" % e)

    def _query_roles(self, *roles):
        roles = "&".join(roles)
        self.log.debug("roles='%s'" % roles)
        r = requests.get("%s/scheduler/%s" % (self.api_uri, roles))
        d = json.loads(r.content.decode())
        r.close()
        d.sort(key=lambda k: k["mac"])
        return d

    def _query_ip_list(self, role):
        self.log.debug("role='%s'" % role)
        r = requests.get("%s/scheduler/ip-list/%s" % (self.api_uri, role))
        d = json.loads(r.content.decode())
        r.close()
        d.sort()
        return d
