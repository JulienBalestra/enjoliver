#!/usr/bin/env python3.5

import argparse
import datetime
import json
import os
import statistics
import sys
import time

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

    def _get_infos_from_raw_query(self, raw: str):
        spl = raw.split("&")
        name = ""
        for i in spl:
            if "mac=" in i:
                mac = i[4:].replace("-", ":")
                req = requests.get("%s/discovery/interfaces" % self.enj_uri)
                req.close()
                content = json.loads(req.content.decode())
                for j in content:
                    if j["mac"] == mac:
                        name = j["fqdn"] if j["fqdn"] else j["ipv4"]
                break
        if not name:
            raise AttributeError("return should be filled")
        return name

    def summarize_locksmith(self):
        lines = list()
        lines.append("Locksmith:")
        for i, ip in enumerate(self.etcd_member_ips):
            try:
                req = requests.get(
                    "http://%s:2379/v2/keys/coreos.com/updateengine/rebootlock/semaphore" % ip)
                req.close()
                if req.status_code == 404:
                    lines.append("  Empty")
                    break
                content = req.content.decode()
                sema = json.loads(content)
                sema = json.loads(sema["node"]["value"])
                holders = sema["holders"] if sema["holders"] else []
                holder_hosts = []
                for h in holders:
                    holder_hosts.append(
                        self._get_infos_from_raw_query(h)
                    )
                lines.append("  Available:  %d/%d" % (sema["semaphore"], sema["max"]))
                lines.append("  Holders:    [%s]" % ",".join(holder_hosts))

            except Exception as e:
                if i + 1 < len(self.etcd_member_ips):
                    continue
                raise
            break
        return lines

    def summarize_etcd_members(self):
        lines = list()
        lines.append("Etcd Members:")
        lines.append("  Kubernetes:")
        for e in self.etcd_member_ips:
            lines.append(" " * 4 + "etcdctl --endpoint http://%s:2379" % e)
        lines.append("  Fleet:")
        for f in self.etcd_member_ips:
            lines.append(" " * 4 + "etcdctl --endpoint http://%s:4001" % f)
        return lines

    def summarize_control_planes(self):
        lines = list()
        lines.append("Kubernetes:")
        for cp in self.k8s_control_plane_ips:
            lines.append("  " + "kubectl -s %s:8080" % cp)
        return lines

    def summarize_fleet(self):
        lines = list()
        lines.append("Fleet:")
        for f in self.etcd_member_ips:
            lines.append("  " + "fleetctl --endpoint=http://%s:4001 --driver=etcd" % f)
        return lines

    def summarize_enjoliver_health(self):
        req = requests.get("%s/healthz" % self.enj_uri)
        req.close()
        content = json.loads(req.content.decode())
        lines = list()
        lines.append("Enjoliver:")
        lines.append("  Healthy" if content["global"] else req.content.decode())
        return lines

    def summarize_lifecycle(self):
        req = requests.get("%s/lifecycle/ignition" % self.enj_uri)
        req.close()
        ignition = json.loads(req.content.decode())
        lines = list()
        up_to_date = 0
        updated_periods = []
        now = datetime.datetime.now()
        for i in ignition:
            if i["up-to-date"] is True:
                up_to_date += 1
                try:
                    updated_date = datetime.datetime.strptime(i["updated_date"], "%a, %d %b %Y %H:%M:%S GMT")
                    if i["last_change_date"] and updated_date + datetime.timedelta(seconds=70) < now:
                        updated_periods.append(
                        datetime.datetime.strptime(i["last_change_date"], "%a, %d %b %Y %H:%M:%S GMT"))
                except TypeError:
                    pass

        updated_periods.sort()
        timedeltas = [updated_periods[i - 1] - updated_periods[i] for i in range(1, len(updated_periods))]
        if timedeltas:
            average_timedelta = sum(timedeltas, datetime.timedelta(0)) / len(timedeltas)
            average_timedelta = datetime.timedelta(microseconds=average_timedelta.microseconds) - average_timedelta

            median_timedelta = statistics.median(timedeltas)
            median_timedelta = datetime.timedelta(microseconds=median_timedelta.microseconds) - median_timedelta

            eta = median_timedelta.seconds * datetime.timedelta(seconds=(len(ignition) - up_to_date))
            eta = (eta + now).strftime("%H:%M") if eta else ""
        else:
            average_timedelta = "-"
            median_timedelta = "-"
            eta = "-"

        req = requests.get("%s/lifecycle/rolling" % self.enj_uri)
        req.close()
        rolling = json.loads(req.content.decode())
        rolling_nb = 0
        for j in rolling:
            if j["enable"] is True:
                rolling_nb += 1

        lines.append("Lifecycle:")
        lines.append("  AutoUpdate:   %d/%d" % (rolling_nb, len(ignition)))
        lines.append("  UpToDate:     %d/%d" % (up_to_date, (len(ignition))))
        lines.append("  AvgUpdate:    %s" % average_timedelta)
        lines.append("  MedUpdate:    %s" % median_timedelta)
        lines.append("  ETA:          %s" % eta)
        return lines

    def _get_ips_of_role(self, role):
        req = requests.get("%s/scheduler/%s" % (self.enj_uri, role))
        req.close()
        schedules = json.loads(req.content.decode())
        ips = []
        for i in schedules:
            ips.append("%s" % i["ipv4"])
        return ips

    def get_all_summaries(self):
        return \
            self.summarize_enjoliver_health() + \
            self.summarize_lifecycle() + \
            self.summarize_locksmith() + \
            [""] + \
            self.summarize_etcd_members() + \
            self.summarize_control_planes() + \
            self.summarize_fleet() + \
            [""]

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
        req.close()
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
            req.close()
            assert req.status_code == 200
            print(" " * 4 + "%d/%d %s" % (i + 1, len(mac), m))
        print("")


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
        '--watch', "-w", type=int, default=0,
        help="Delay between polling"
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
        enjoliver.summarize_enjoliver_health()
        enjoliver.restore_schedule_of()
        enjoliver.get_all_summaries()
    elif task == "ls":
        delay = parser.parse_args().watch
        if delay:
            watch = ""
            while True:
                try:
                    summary = enjoliver.get_all_summaries()
                    if summary != watch:
                        print("\n" + "-" * (len(max(summary, key=len)) + 1))
                        print("\n".join(summary))
                        watch = summary

                    os.write(1, b"\r")
                    print("-> %s next watch in %ds" % (datetime.datetime.now().strftime("%H:%M:%S"), delay), end="")
                    sys.stdout.flush()
                    time.sleep(delay)
                except KeyboardInterrupt:
                    os.write(1, b"\nExited\n")
                    break
        else:
            print("\n".join(enjoliver.get_all_summaries()), end='')
