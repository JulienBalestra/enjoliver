"""
Schedule the roles with the given constraints
"""
import abc
import json
import time

import requests

import logging
from configs import EnjoliverConfig
from model import ScheduleRoles

EC = EnjoliverConfig(importer=__file__)

logger = logging.getLogger(__name__)


class CommonScheduler(object):
    """
    Base class to create profiles with deps
    """
    __metaclass__ = abc.ABCMeta
    apply_deps_tries = EC.apply_deps_tries
    apply_deps_delay = EC.apply_deps_delay

    @staticmethod
    def fetch_available(api_uri: str):
        """
        HTTP Get to the <api_uri>/scheduler/available
        :param api_uri: str
        :return: list of interfaces
        """
        query = "%s/scheduler/available" % api_uri
        logger.debug("fetch %s" % query)
        try:
            r = requests.get(query)
            interfaces = json.loads(r.content.decode())
            r.close()
            logger.debug("fetch done with len(%d)" % len(interfaces))
            return interfaces
        except requests.exceptions.ConnectionError:
            logger.error("fetch failed: %s" % query)
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
        logger.info("tries:%d delay:%d" % (self.apply_deps_tries, self.apply_deps_delay))
        for t in range(self.apply_deps_tries):
            if dep_instance.apply() is True:
                return True
            time.sleep(self.apply_deps_delay)

        logger.error("timeout after %d" % (self.apply_deps_delay * self.apply_deps_tries))
        raise RuntimeError("timeout after %d" % (
            self.apply_deps_delay * self.apply_deps_tries))

    def _affect(self, available: dict):
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
        logger.info("mac:%s roles:%s" % (mac, str(self.roles)))
        return 1

    def __apply_available_budget(self):
        available_list = self.fetch_available(self.api_uri)
        if len(available_list) >= self.expected_nb:
            logger.info("starting...")
            available_list.sort(key=lambda k: k["mac"])
            for i in range(self.expected_nb):
                self._affect(available_list[i])
            return True

        else:
            logger.info("not enough item %d/%d" % (len(available_list), self.expected_nb))
            return False

    def _apply_budget(self):
        url = "%s/scheduler/%s" % (self.api_uri, "&".join(self.roles))
        try:
            r = requests.get(url)
            done = json.loads(r.content.decode())
            r.close()
            if len(done) != self.expected_nb:
                logger.info("%s -> done:%d expected:%d" % ("&".join(self.roles), len(done), self.expected_nb))
            if len(done) < self.expected_nb:
                logger.debug("%d < %d" % (len(done), self.expected_nb))
                return self.__apply_available_budget()

            return True
        except (requests.exceptions.ConnectionError, ValueError):
            logger.error("ConnectionError %s" % url)
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
                logger.info("%s -> done:%d available:%d" % ("&".join(self.roles), done, len(available_list)))
            for available in available_list:
                done += self._affect(available)

            return done
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError %s" % url)
            return 0

    def _apply_with_retry(self, apply_fn, nb_try: int, seconds_sleep: int):
        for i in range(nb_try):
            try:
                return apply_fn()
            except Exception as e:
                logger.error("fail to apply the schedule %s %s" % (type(e), e))
                if i + 1 == nb_try:
                    raise

            logger.warning("retry %d/%d in %d s" % (i + 1, nb_try, seconds_sleep))
            time.sleep(seconds_sleep)


class EtcdMemberKubernetesControlPlane(CommonScheduler):
    expected_nb = EC.etcd_member_kubernetes_control_plane_expected_nb
    roles = [ScheduleRoles.etcd_member, ScheduleRoles.kubernetes_control_plane]
    roles.sort()
    __name__ = "".join(roles)

    def __init__(self,
                 api_uri: str):
        logger.info("with api_uri %s" % api_uri)
        self.api_uri = api_uri

    def apply(self, nb_try=2, seconds_sleep=0):
        return self._apply_with_retry(self._apply_budget, nb_try=nb_try, seconds_sleep=seconds_sleep)


class KubernetesNode(CommonScheduler):
    roles = [ScheduleRoles.kubernetes_node]
    roles.sort()
    __name__ = "".join(roles)

    def __init__(self,
                 api_uri: str,
                 apply_dep):
        logger.info("with api_uri %s" % api_uri)
        self.api_uri = api_uri

        if apply_dep is True:
            logger.info("applying deps by instancing %s" % EtcdMemberKubernetesControlPlane.__name__)
            sch_cp = EtcdMemberKubernetesControlPlane(self.api_uri)
            self.apply_dep(sch_cp)

    def apply(self, nb_try=2, seconds_sleep=0):
        return self._apply_with_retry(self._apply_everything, nb_try=nb_try, seconds_sleep=seconds_sleep)
