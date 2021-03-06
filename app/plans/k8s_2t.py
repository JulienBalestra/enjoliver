#! /usr/bin/env python3
import json
import logging
import os

import requests
import sys
import time

try:
    import generator
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import generator

import schedulerv2
import sync

from configs import EnjoliverConfig

logger = logging.getLogger(__file__)

EC = EnjoliverConfig(importer=__file__)


class Kubernetes2Tiers(object):
    """
    Kubernetes 2 tiers is a plan class for creating control plane and nodes
    It run a simple scheduler and a sync state of matchbox
    """
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
        if EC.extra_selectors:
            extra_selectors = "&".join(["%s=%s" % (k, v) for k, v in EC.extra_selectors.items()])
        else:
            extra_selectors = ""
        extra_md = {
            "etc_hosts": EC.etc_hosts,
            "extra_selectors": extra_selectors,
            "coreos_install_base_url": EC.coreos_install_base_url,
        }
        if EC.lldp_image_url:
            logger.debug("adding lldp_image_url: %s" % EC.lldp_image_url)
            extra_md.update({"lldp_image_url": EC.lldp_image_url})
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="discovery",
            name="discovery",
            ignition_id="%s.yaml" % self.ignition_dict["discovery"],
            matchbox_path=self.matchbox_path,
            extra_metadata=extra_md,
            pxe_redirect=True
        )
        gen.dumps()

    def apply(self):
        """
        Schedule and synchronise the state for matchbox
        :return: the number of synchronised machines
        """
        while self._sch_k8s_control_plane.apply(nb_try=5, seconds_sleep=1) is False:
            time.sleep(self.wait)

        self._sch_k8s_node.apply(nb_try=5, seconds_sleep=1)
        return self._sync.apply(nb_try=10, seconds_sleep=2)

    @property
    def etcd_member_ip_list(self):
        return self._sync.etcd_member_ip_list

    @property
    def kubernetes_control_plane_ip_list(self):
        return self._sync.kubernetes_control_plane_ip_list

    @property
    def kubernetes_nodes_ip_list(self):
        return self._sync.kubernetes_nodes_ip_list


def is_health_for_plan(healthz: dict):
    """
    Healthy for starting the plan class
    :param healthz:
    :return: bool
    """
    if healthz["global"] is True:
        return True

    if healthz["db"] is True and healthz["matchbox"]["/"] is True:
        return True

    return False


if __name__ == '__main__':
    logging.basicConfig(level=EC.logging_level, stream=sys.stderr, format=EC.logging_formatter)

    health = "%s/healthz" % EC.api_uri
    tries = 10
    for i in range(tries):
        try:
            r = requests.get(health)
            content = r.content.decode()
            s = json.loads(content)
            # we only want the database and matchbox be ready
            status = is_health_for_plan(s)
            if status is True:
                logger.info("%d/%d status for plan is %s" % (i, tries, status))
                break
            logger.warning("%d/%d status for plan is %s" % (i, tries, status))
        except Exception as e:
            logger.error("%d/%d [%s] returned -> %s" % (i, tries, health, e))
            if i == tries - 1:
                raise
        time.sleep(5)

    k2t = Kubernetes2Tiers(
        ignition_dict=EC.ignition_dict,
        matchbox_path=EC.matchbox_path,
        api_uri=EC.api_uri,
        extra_selectors=EC.extra_selectors
    )

    wait = 10
    if EC.sync_cache_ttl > 0:
        wait = EC.sync_cache_ttl + (EC.sync_cache_ttl * 0.1)
        logger.info("cache_ttl is set at %ds, using %ds as sleep interval" % (EC.sync_cache_ttl, wait))
    else:
        logger.warning("no cache_ttl is set switching to default sleep %ds" % wait)

    while True:
        k2t.apply()
        time.sleep(wait)
