import json
import os
import urllib2

import generator


class EtcdScheduler(object):
    etcd_members_nb = 3
    __name__ = "EtcdScheduler"
    etcd_name = "static"  # basename

    def __init__(self,
                 api_endpoint, bootcfg_path,
                 ignition_member, ignition_proxy,
                 bootcfg_prefix=""):

        self.api_endpoint = api_endpoint
        self.gen = generator.Generator
        self.bootcfg_path = bootcfg_path
        self._pending_etcd_member = set()
        self._done_etcd_member = set()
        self.bootcfg_prefix = bootcfg_prefix
        # self.scheduler_model = self.
        self.ignition_member = ignition_member
        self.ignition_proxy = ignition_proxy

    @staticmethod
    def fetch_interfaces(api_endpoint):
        os.write(2, "\r-> fetch %s\n\r" % api_endpoint)
        content = urllib2.urlopen("%s/discovery/interfaces" % api_endpoint)
        response_body = content.read()
        content.close()
        interfaces = json.loads(response_body)
        os.write(2, "\r-> fetch done\n\r")
        return interfaces

    def _fifo_members(self, interfaces):

        if interfaces["interfaces"] is None:
            os.write(2, "\r-> no machine 0/%d\n\r" % self.etcd_members_nb)
            return self._pending_etcd_member

        elif len(interfaces["interfaces"]) < self.etcd_members_nb:
            os.write(2, "\r-> not enough machines %d/%d\n\r" % (
                len(interfaces["interfaces"]), self.etcd_members_nb))
            return self._pending_etcd_member

        else:
            for machine in interfaces["interfaces"]:
                # each machine with 2 interfaces [lo, eth0]
                if len(machine) > 2:
                    # Scheduler is stupid
                    raise AttributeError("too much interfaces, which one choose ?")
                for nic in machine:
                    if nic["name"] == "lo":
                        continue
                    elif len(self._pending_etcd_member) < self.etcd_members_nb:
                        self._pending_etcd_member.add((nic["IPv4"], nic["MAC"]))
                    else:
                        os.write(2, "\r-> enough machines %d/%d\n\r" % (
                            len(interfaces["interfaces"]), self.etcd_members_nb))
                        return self._pending_etcd_member

        os.write(2, "\r-> enough machines %d/%d\n\r" % (len(interfaces["interfaces"]), self.etcd_members_nb))
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
            self.gen = generator.Generator(
                group_id="%s-%d" % (marker, i),  # one per machine
                profile_id=marker,  # link to ignition
                name="%s-%d" % (marker, i),
                ignition_id="%s.yaml" % self.ignition_member,
                bootcfg_path=self.bootcfg_path,
                selector={"mac": nic[1]},
                extra_metadata={
                    "etcd_name": "%s%d" % (self.etcd_name, i),
                    "etcd_initial_cluster": etcd_initial_cluster,
                    "etcd_initial_advertise_peer_urls": "http://%s:2380" % nic[0],
                    "etcd_advertise_client_urls": "http://%s:2379" % nic[0],

                }
            )
            self.gen.dumps()
            self._done_etcd_member.add(nic)
            os.write(2, "\r-> %s.%s selector {mac: %s}\n\r" % (
                self.__name__, self._apply_member.__name__, nic))

    def apply(self):
        # Etcd Members
        if len(self._done_etcd_member) < self.etcd_members_nb:
            interfaces = self.fetch_interfaces(self.api_endpoint)
            self._fifo_members(interfaces)
            if len(self._pending_etcd_member) == self.etcd_members_nb:
                self._apply_member()

        else:
            # TODO Etcd Proxy
            os.write(2, "\r-> %s.%s already complete\n\r" %
                     (self.__name__, self.apply.__name__))
            return True

        if len(self._done_etcd_member) < self.etcd_members_nb:
            return False
        else:
            os.write(2, "\r-> %s.%s complete\n\r" %
                     (self.__name__, self.apply.__name__))
            return True
