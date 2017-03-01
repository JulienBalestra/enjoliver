import abc
import json
import time

import requests

import logger
from configs import EnjoliverConfig
from model import ScheduleRoles

ec = EnjoliverConfig(importer=__file__)


class CommonScheduler(object):
    """
    Base class to create profiles with deps
    """
    __metaclass__ = abc.ABCMeta

    log = logger.get_logger(__file__)

    apply_deps_tries = ec.apply_deps_tries
    apply_deps_delay = ec.apply_deps_delay

    @staticmethod
    def fetch_available(api_uri):
        """
        HTTP Get to the <api_uri>/scheduler/available
        :param api_uri: str
        :return: list of interfaces
        """
        query = "%s/scheduler/available" % api_uri
        CommonScheduler.log.debug("fetch %s" % query)
        try:
            r = requests.get(query)
            interfaces = json.loads(r.content.decode())
            r.close()
            CommonScheduler.log.debug("fetch done with len(%d)" % len(interfaces))
            return interfaces
        except requests.exceptions.ConnectionError:
            CommonScheduler.log.error("fetch failed: %s" % query)
            return []

    @abc.abstractmethod
    def apply(self):
        """
        Entrypoint to apply the schedule plan
        >>> sch = CommonScheduler()
        >>> sch.apply()
        :return: True if it's a number require
            (3 members for Etcd), int number of effective apply (Etcd Proxy)
        """

    def apply_dep(self, dep_instance):
        self.log.info("tries:%d delay:%d" % (self.apply_deps_tries, self.apply_deps_delay))
        for t in range(self.apply_deps_tries):
            if dep_instance.apply() is True:
                return True
            time.sleep(self.apply_deps_delay)

        self.log.error("timeout after %d" % (self.apply_deps_delay * self.apply_deps_tries))
        raise RuntimeError("timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries))

    def _affect(self, available):
        mac = available["mac"]
        r = requests.post("%s/scheduler" % self.api_uri, data=json.dumps(
            {
                "roles": self.roles,
                "selector": {
                    "mac": mac,
                }
            }
        ))
        r.close()
        self.log.info("mac:%s roles:%s" % (mac, str(self.roles)))
        return 1

    def __apply_available_budget(self):
        available_list = self.fetch_available(self.api_uri)
        if len(available_list) >= self.expected_nb:
            self.log.info("starting...")
            available_list.sort(key=lambda k: k["mac"])
            for i in range(self.expected_nb):
                self._affect(available_list[i])
            return True

        else:
            self.log.info("not enough item %d/%d" % (len(available_list), self.expected_nb))
            return False

    def _apply_budget(self):
        url = "%s/scheduler/%s" % (self.api_uri, "&".join(self.roles))
        try:
            r = requests.get(url)
            done = json.loads(r.content.decode())
            r.close()
            if len(done) != self.expected_nb:
                self.log.info("%s -> done:%d expected:%d" % ("&".join(self.roles), len(done), self.expected_nb))
            if len(done) < self.expected_nb:
                self.log.debug("%d < %d" % (len(done), self.expected_nb))
                return self.__apply_available_budget()

            return True
        except (requests.exceptions.ConnectionError, ValueError):
            self.log.error("ConnectionError %s" % url)
            return False

    def _apply_everything(self):
        url = "%s/scheduler/%s" % (self.api_uri, "&".join(self.roles))
        try:
            r = requests.get(url)
            done = len(json.loads(r.content.decode()))
            r.close()
            available_list = self.fetch_available(self.api_uri)
            available_list.sort(key=lambda k: k["mac"])
            if available_list:
                self.log.info("%s -> done:%d available:%d" % ("&".join(self.roles), done, len(available_list)))
            for available in available_list:
                done += self._affect(available)

            return done
        except requests.exceptions.ConnectionError:
            self.log.error("ConnectionError %s" % url)
            return 0


class EtcdMemberKubernetesControlPlane(CommonScheduler):
    expected_nb = ec.etcd_member_kubernetes_control_plane_expected_nb
    roles = [ScheduleRoles.etcd_member, ScheduleRoles.kubernetes_control_plane]
    roles.sort()
    __name__ = "".join(roles)

    def __init__(self,
                 api_uri):
        self.log.info("with api_uri %s" % api_uri)
        self.api_uri = api_uri

    def apply(self):
        return self._apply_budget()


class KubernetesNode(CommonScheduler):
    roles = [ScheduleRoles.kubernetes_node]
    roles.sort()
    __name__ = "".join(roles)

    def __init__(self,
                 api_uri,
                 apply_dep):
        self.log.info("with api_uri %s" % api_uri)
        self.api_uri = api_uri

        if apply_dep is True:
            self.log.info("applying deps by instancing %s" % EtcdMemberKubernetesControlPlane.__name__)
            sch_cp = EtcdMemberKubernetesControlPlane(self.api_uri)
            self.apply_dep(sch_cp)

    def apply(self):
        return self._apply_everything()
