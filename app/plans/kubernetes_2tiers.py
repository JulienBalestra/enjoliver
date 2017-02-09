#! /usr/bin/env python
import os
import sys

import time

try:
    import generator
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import generator

import schedulerv2
import sync_bootcfg


class Kubernetes2Tiers(object):
    wait = 10

    def __init__(self,
                 ignition_dict,
                 bootcfg_path="/var/lib/bootcfg",
                 api_uri="http://127.0.0.1:5000",
                 extra_selectors=None):
        self.api_uri = api_uri
        self.ignition_dict = ignition_dict
        self.bootcfg_path = bootcfg_path

        self._init_discovery()

        self._sch_k8s_control_plane = schedulerv2.EtcdMemberKubernetesControlPlane(self.api_uri)
        self._sch_k8s_node = schedulerv2.KubernetesNode(self.api_uri, apply_dep=False)

        self._sync = sync_bootcfg.ConfigSyncSchedules(self.api_uri, self.bootcfg_path, self.ignition_dict,
                                                      extra_selectors)

    def _init_discovery(self):
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="discovery",
            name="discovery",
            ignition_id="%s.yaml" % self.ignition_dict["discovery"],
            bootcfg_path=self.bootcfg_path
        )
        gen.dumps()

    def apply(self):
        while self._sch_k8s_control_plane.apply() is False:
            time.sleep(self.wait)
        nb = self._sch_k8s_node.apply()
        self._sync.apply()
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
    from configs import EnjoliverConfig

    ec = EnjoliverConfig()

    k2t = Kubernetes2Tiers(
        ignition_dict=ec.ignition_dict,
        bootcfg_path=ec.bootcfg_path,
        api_uri=ec.api_uri,
        extra_selectors=ec.extra_selectors
    )
    while True:
        k2t.apply()
        time.sleep(120)
