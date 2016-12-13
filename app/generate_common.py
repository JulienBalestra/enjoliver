import json
import os
import subprocess
import re
import sys
import abc

import logger


class GenerateCommon(object):
    """
    Common set of methods used to generate groups and profiles
    """

    __metaclass__ = abc.ABCMeta

    app_path = "%s" % os.path.dirname(__file__)
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path

    _target_data = None

    _bootcfg_ip = None
    _bootcfg_port = int(os.getenv("BOOTCFG_PORT", "8080"))

    _api_ip = None
    _api_port = int(os.getenv("API_PORT", "5000"))  # Flask

    _raise_enof = IOError

    log = logger.get_logger("Generator")

    @abc.abstractmethod
    def generate(self):
        return

    @property
    def target_data(self):
        if self._target_data is not None:
            return self._target_data
        return self.generate()

    def get_ip_from_setup_network_environment(self):
        # This only work on Linux and if the DEFAULT_IPV4 is listening bootcfg address
        out = "%s/misc/network-environment" % self.bootcfg_path
        subprocess.check_call(
            ["%s/assets/setup-network-environment/serve/setup-network-environment" %
             self.bootcfg_path, "-o", "%s" % out])
        with open("%s" % out, mode='r') as fd:
            for l in fd:
                if "DEFAULT_IPV4=" in l:
                    ip = l.split("DEFAULT_IPV4=")[1].replace("\n", "")
                    match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
                    if match is not None:
                        self.log.debug("correct IP address")
                        return ip
                    self.log.error("ERROR incorrect IP address")
        raise ImportError("Error in module %s" % out)

    @property
    def api_ip(self):
        """
        :rtype: str
        :return: IP address
        """
        if self._api_ip is not None:
            self.log.debug("return %s" % self._api_ip)
            return self._api_ip
        api_ip = os.getenv("API_IP")
        if api_ip and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", api_ip):
            self._api_ip = api_ip
            self.log.debug("env -> API_IP=%s" % self._api_ip)
        else:
            self._api_ip = self.get_ip_from_setup_network_environment()

        return self._api_ip

    @property
    def bootcfg_ip(self):
        """
        :rtype: str
        :return: IP address
        """
        if self._bootcfg_ip is not None:
            self.log.debug("return %s" % self._bootcfg_ip)
            return self._bootcfg_ip
        bootcfg_ip = os.getenv("BOOTCFG_IP")
        if bootcfg_ip and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", bootcfg_ip):
            self._bootcfg_ip = bootcfg_ip
            self.log.debug("env -> BOOTCFG_IP=%s" % self._api_ip)
        else:
            self._bootcfg_ip = self.get_ip_from_setup_network_environment()

        return self._bootcfg_ip

    @property
    def api_uri(self):
        return "http://%s:%s" % (self.api_ip, self._api_port)

    @property
    def bootcfg_uri(self):
        return "http://%s:%s" % (self.bootcfg_ip, self._bootcfg_port)

    def render(self, indent=2):
        self.generate()
        return json.dumps(self._target_data, indent=indent)

    def dump(self):
        with open("%s/%s.json" % (self.target_path, self.target_data["id"]), "w") as fd:
            fd.write(self.render())

    @staticmethod
    def ensure_directory(path):
        if os.path.isdir(path) is False:
            raise IOError("%s not a valid as directory" % path)
        return path

    def ensure_file(self, path):
        if os.path.isfile(path) is False:
            raise self._raise_enof("%s not a valid as file" % path)
        return path
