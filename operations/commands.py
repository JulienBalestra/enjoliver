#!/usr/bin/env python3.5

import argparse
import json
import os

import requests
from kubernetes import client as kc


class EnjoliverCommandLine(object):
    def __init__(self, enjoliver_uri, kubernetes_apiserver):
        self.enj_uri = enjoliver_uri
        self.k8s_uri = kubernetes_apiserver

        self._etcd_members_ips = []
        self._k8s_control_plane_ips = []

    @property
    def etcd_member_ips(self):
        if not self._etcd_members_ips:
            self._etcd_members_ips = self._get_ips_of_role("etcd-member")
        return self._etcd_members_ips

    @property
    def k8s_control_plane_ips(self):
        if not self._k8s_control_plane_ips:
            self._k8s_control_plane_ips = self._get_ips_of_role("kubernetes-control-plane")
        return self._k8s_control_plane_ips

    def display_etcd_members(self):
        print(
            "Etcd Members:\n",
            "  Kubernetes:\n",
            " " * 4 + "\n".join(["etcdctl --endpoint http://%s:2379" % k for k in self.etcd_member_ips]),
            "\n"
            "  Fleet:\n",
            " " * 4 + "\n".join(["etcdctl --endpoint http://%s:4001" % k for k in self.etcd_member_ips]),
            end="\n\n"
        )

    def display_control_planes(self):
        print(
            "Kubernetes:\n",
            " " * 2 + "\n".join(["kubectl -s %s:8080" % k for k in self.k8s_control_plane_ips]),
            end="\n\n"

        )

    def display_fleet(self):
        print(
            "Fleet:\n",
            " " * 2 + "\n".join(["fleetctl --endpoint=http://%s:4001 --driver=etcd" % k for k in self.etcd_member_ips]),
            end="\n\n"
        )

    def display_enjoliver_health(self):
        req = requests.get("%s/healthz" % self.enj_uri)
        content = json.loads(req.content.decode())
        print(
            "Enjoliver Status:\n",
            "  Healthy" if content["global"] else print(req.content.decode()), end="\n\n")

    def _get_ips_of_role(self, role):
        req = requests.get("%s/scheduler/%s" % (self.enj_uri, role))
        schedules = json.loads(req.content.decode())
        ips = []
        for i in schedules:
            ips.append("%s" % i["ipv4"])
        return ips

    def display(self):
        self.display_enjoliver_health()
        self.display_etcd_members()
        self.display_control_planes()
        self.display_fleet()

    @property
    def k8s_apiserver_endpoint(self):
        if self.k8s_uri:
            return self.k8s_uri
        return "%s:8080" % self.k8s_control_plane_ips[0]

    def _find_mac_address_of_nodes(self, label):
        c = kc.ApiClient(host=self.k8s_apiserver_endpoint)
        core = kc.CoreV1Api(c)
        match = []
        for n in core.list_node().items:
            try:
                if n.metadata.labels[label] == "true":
                    for a in n.status.addresses:
                        if a.type == 'InternalIP':
                            match.append(a.address)
            except KeyError:
                pass
        mac = []
        req = requests.get("%s/discovery/interfaces" % self.enj_uri)
        for m in json.loads(req.content.decode()):
            if m["as_boot"] is True and m["ipv4"] in match:
                mac.append(m["mac"])
        return mac

    def restore_schedule_of(self, roles="etcd-member,kubernetes-control-plane"):
        print("%s:\n  %s" % (self.restore_schedule_of.__name__, roles))
        mac = self._find_mac_address_of_nodes("control-plane")
        for i, m in enumerate(mac):
            data = json.dumps({
                u"roles": roles.split(","),
                u'selector': {
                    u"mac": m
                }
            })
            req = requests.post("%s/scheduler" % self.enj_uri, data=data)
            assert req.status_code == 200
            print(" " * 4 + "%d/%d %s" % (i + 1, len(mac), m))
        print("")
        self.display()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Enjoliver-cli')
    parser.add_argument(
        '--enjoliver', type=str, default=os.getenv("ENJOLIVER", 'http://172.20.0.1:5000'),
        help="Enjoliver endpoint 'http://172.20.0.1:5000'"
    )
    parser.add_argument(
        '--kapiserver', type=str, default="",
        help="Kubernetes api-server endpoint 172.20.0.2:8080"
    )
    parser.add_argument(
        'task', type=str, default="display",
        help="Task to run [ls, restore]"
    )
    enjoliver = EnjoliverCommandLine(
        enjoliver_uri=parser.parse_args().enjoliver,
        kubernetes_apiserver=parser.parse_args().kapiserver,
    )
    task = parser.parse_args().task
    if task == "restore":
        enjoliver.display_enjoliver_health()
        enjoliver.restore_schedule_of()
    elif task == "ls":
        enjoliver.display()
