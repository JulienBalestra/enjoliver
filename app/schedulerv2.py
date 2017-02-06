import abc
import json
import time
import urllib2

import requests

import logger
from model import ScheduleRoles


class CommonScheduler(object):
    """
    Base class to create profiles with deps
    """
    __metaclass__ = abc.ABCMeta

    log = logger.get_logger(__file__)

    apply_deps_tries = 15
    apply_deps_delay = 60

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
        CommonScheduler.log.info("fetch %s" % api_uri)
        content = urllib2.urlopen("%s/scheduler/available" % api_uri)
        response_body = content.read()
        content.close()
        interfaces = json.loads(response_body)
        CommonScheduler.log.info("fetch done with len(%d)" % len(interfaces))
        return interfaces

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
        r = requests.get("%s/scheduler/%s" % (self.api_uri, "&".join(self.roles)))
        done = json.loads(r.content)
        r.close()
        self.custom_log(self.apply.__name__, "done:%d expected:%d" % (len(done), self.expected_nb))
        if len(done) < self.expected_nb:
            self.custom_log(self.apply.__name__, "%d < %d" % (len(done), self.expected_nb))
            return self.__apply_available_budget()

        return True

    def _apply_everything(self):
        done = 0
        available_list = self.fetch_available(self.api_uri)
        for available in available_list:
            done += self._affect(available)
        return done


class EtcdMemberKubernetesControlPlane(CommonScheduler):
    expected_nb = 3
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
                 apply_dep=True):
        self.custom_log("%s.__init__" % self.__name__,
                        "with api_uri %s" % api_uri)
        self.api_uri = api_uri

        if apply_dep:
            self.custom_log("%s.__init__" % self.__name__,
                            "applying deps by instancing %s" % EtcdMemberKubernetesControlPlane.__name__)
            sch_cp = EtcdMemberKubernetesControlPlane(self.api_uri)
            self.apply_dep(sch_cp)

    def apply(self):
        return self._apply_everything()
