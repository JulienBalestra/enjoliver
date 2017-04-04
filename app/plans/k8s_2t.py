#! /usr/bin/env python
import json
import os
import sys
import time

import requests

try:
    import generator
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import generator

import schedulerv2
import sync
import logger

from configs import EnjoliverConfig


class Kubernetes2Tiers(object):
    wait = 10

    def __init__(self,
                 ignition_dict,
                 matchbox_path="/var/lib/matchbox",
                 api_uri="http://127.0.0.1:5000",
                 extra_selectors=None):
        self.api_uri = api_uri
        self.ignition_dict = ignition_dict
        self.matchbox_path = matchbox_path

        self._init_discovery()

        self._sch_k8s_control_plane = schedulerv2.EtcdMemberKubernetesControlPlane(self.api_uri)
        self._sch_k8s_node = schedulerv2.KubernetesNode(self.api_uri, apply_dep=False)

        self._sync = sync.ConfigSyncSchedules(self.api_uri, self.matchbox_path, self.ignition_dict,
                                              extra_selectors)

    def _init_discovery(self):
        local_ec = EnjoliverConfig(importer=__file__)
        if local_ec.extra_selectors:
            extra_selectors = "&".join(["%s=%s" % (k, v) for k, v in local_ec.extra_selectors.items()])
        else:
            extra_selectors = ""
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="discovery",
            name="discovery",
            ignition_id="%s.yaml" % self.ignition_dict["discovery"],
            matchbox_path=self.matchbox_path,
            extra_metadata={
                "lldp_image_url": local_ec.lldp_image_url,
                "etc_hosts": local_ec.etc_hosts,
                "extra_selectors": extra_selectors,
                "coreos_install_base_url": local_ec.coreos_install_base_url,
            }
        )
        gen.dumps()

    def apply(self):
        while self._sch_k8s_control_plane.apply(nb_try=5, seconds_sleep=1) is False:
            time.sleep(self.wait)
        nb = self._sch_k8s_node.apply(nb_try=5, seconds_sleep=1)
        self._sync.apply(nb_try=10, seconds_sleep=2)
        return nb

    @property
    def etcd_member_ip_list(self):
        return self._sync.etcd_member_ip_list

    @property
    def kubernetes_control_plane_ip_list(self):
        return self._sync.kubernetes_control_plane_ip_list

    @property
    def kubernetes_nodes_ip_list(self):
        return self._sync.kubernetes_nodes_ip_list


if __name__ == '__main__':
    log = logger.get_logger(__file__)
    wait = 30
    ec = EnjoliverConfig(importer=__file__)
    Kubernetes2Tiers.wait = wait

    health = "%s/healthz" % ec.api_uri
    tries = 10
    for i in range(tries):
        try:
            r = requests.get(health)
            content = r.content.decode()
            s = json.loads(content)
            if s["global"] is True:
                log.info("%d/%d Global status is %s" % (i, tries, s["global"]))
                break
            log.warning("%d/%d Global status is %s" % (i, tries, s["global"]))
        except Exception as e:
            log.error("%d/%d [%s] returned -> %s" % (i, tries, health, e))
        time.sleep(5)

    k2t = Kubernetes2Tiers(
        ignition_dict=ec.ignition_dict,
        matchbox_path=ec.matchbox_path,
        api_uri=ec.api_uri,
        extra_selectors=ec.extra_selectors
    )
    while True:
        k2t.apply()
        time.sleep(k2t.wait)
