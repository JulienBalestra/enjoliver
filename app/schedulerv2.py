import abc
import json
import time

import requests

import logger
from configs import EnjoliverConfig
from model import ScheduleRoles

ec = EnjoliverConfig()


class CommonScheduler(object):
    """
    Base class to create profiles with deps
    """
    __metaclass__ = abc.ABCMeta

    log = logger.get_logger(__file__)

    apply_deps_tries = ec.apply_deps_tries
    apply_deps_delay = ec.apply_deps_delay

    def custom_log(self, func_name, message, level="info"):
        """
        Custom log method
        :param func_name: func.__name__
        :param message: message to display
        :param level: log level (will be lower() anyway)
        :return: None
        """
        if level.lower() == "debug":
            self.log.debug("%s.%s %s" % (self.__name__, func_name, message))
        elif level.lower() == "warning":
            self.log.warning("%s.%s %s" % (self.__name__, func_name, message))
        elif level.lower() == "error":
            self.log.warning("%s.%s %s" % (self.__name__, func_name, message))
        else:
            self.log.info("%s.%s %s" % (self.__name__, func_name, message))

    @staticmethod
    def fetch_available(api_uri):
        """
        HTTP Get to the <api_uri>/scheduler/available
        :param api_uri: str
        :return: list of interfaces
        """
        query = "%s/scheduler/available" % api_uri
        CommonScheduler.log.info("fetch %s" % query)
        try:
            r = requests.get(query)
            interfaces = json.loads(r.content)
            r.close()
            CommonScheduler.log.info("fetch done with len(%d)" % len(interfaces))
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
        self.custom_log(self.apply_dep.__name__, "tries:%d delay:%d" % (self.apply_deps_tries, self.apply_deps_delay))
        for t in xrange(self.apply_deps_tries):
            if dep_instance.apply() is True:
                return True
            time.sleep(self.apply_deps_delay)

        self.custom_log(self.apply_dep.__name__, "timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries), "error")
        raise RuntimeError("timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries))

    def _affect(self, available):
        mac = available["mac"]
        self.custom_log(self._affect.__name__, "affecting mac:%s" % mac)
        r = requests.post("%s/scheduler" % self.api_uri, data=json.dumps(
            {
                "roles": self.roles,
                "selector": {
                    "mac": mac,
                }
            }
        ))
        r.close()
        self.custom_log(self._affect.__name__, "affected mac:%s" % mac)
        return 1

    def __apply_available_budget(self):
        available = self.fetch_available(self.api_uri)
        if len(available) >= self.expected_nb:
            self.custom_log(self.__apply_available_budget.__name__, "starting...")
            for i in range(self.expected_nb):
                self._affect(available[i])
            return True

        else:
            self.custom_log(self.__apply_available_budget.__name__, "not enough item")
            return False

    def _apply_budget(self):
        url = "%s/scheduler/%s" % (self.api_uri, "&".join(self.roles))
        try:
            r = requests.get(url)
            done = json.loads(r.content)
            r.close()
            self.custom_log(self.apply.__name__, "done:%d expected:%d" % (len(done), self.expected_nb))
            if len(done) < self.expected_nb:
                self.custom_log(self.apply.__name__, "%d < %d" % (len(done), self.expected_nb))
                return self.__apply_available_budget()

            return True
        except requests.exceptions.ConnectionError:
            self.custom_log(self.apply.__name__, "ConnectionError %s" % url)
            return False

    def _apply_everything(self):
        url = "%s/scheduler/%s" % (self.api_uri, "&".join(self.roles))
        try:
            r = requests.get(url)
            done = len(json.loads(r.content))
            r.close()
            available_list = self.fetch_available(self.api_uri)
            self.custom_log(self.apply.__name__, "done:%d available:%d" % (done, len(available_list)))
            for available in available_list:
                done += self._affect(available)

            return done
        except requests.exceptions.ConnectionError:
            self.custom_log(self.apply.__name__, "ConnectionError %s" % url)
            return 0


class EtcdMemberKubernetesControlPlane(CommonScheduler):
    expected_nb = ec.etcd_member_kubernetes_control_plane_expected_nb
    roles = [ScheduleRoles.etcd_member, ScheduleRoles.kubernetes_control_plane]
    __name__ = "EtcdMemberKubernetesControlPlane"

    def __init__(self,
                 api_uri):
        self.custom_log("%s.__init__" % self.__name__,
                        "with api_uri %s" % api_uri)
        self.api_uri = api_uri

    def apply(self):
        return self._apply_budget()


class KubernetesNode(CommonScheduler):
    roles = [ScheduleRoles.kubernetes_node]
    __name__ = "KubernetesNode"

    def __init__(self,
                 api_uri,
                 apply_dep):
        self.custom_log("%s.__init__" % self.__name__,
                        "with api_uri %s" % api_uri)
        self.api_uri = api_uri

        if apply_dep is True:
            self.custom_log("%s.__init__" % self.__name__,
                            "applying deps by instancing %s" % EtcdMemberKubernetesControlPlane.__name__)
            sch_cp = EtcdMemberKubernetesControlPlane(self.api_uri)
            self.apply_dep(sch_cp)

    def apply(self):
        return self._apply_everything()
