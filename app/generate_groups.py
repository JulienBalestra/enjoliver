import re

from generate_common import GenerateCommon


class GenerateGroup(GenerateCommon):
    def __init__(self, _id, name, profile, selector=None,
                 bootcfg_path=GenerateCommon.bootcfg_path):
        self.target_path = "%s/groups" % bootcfg_path
        self.selector = selector

        self._ip_address = None
        self._target_data = {
            "id": _id,
            "name": name,
            "profile": profile,
            "metadata": {
                "seed": "",
                "etcd_initial_cluster": ""
            }
        }

    def _metadata(self):
        self._target_data["metadata"]["seed"] = "http://%s:8080" % self.ip_address
        self._target_data["metadata"]["etcd_initial_cluster"] = ""

    def _selector(self):
        if self.selector is None:
            return

        if type(self.selector) is not dict:
            raise TypeError("selector is not a dict")

        try:
            self.selector["mac"] = self.selector["mac"].lower()
            match = re.match(r"^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$",
                             self.selector["mac"])
            if match is None:
                raise TypeError("%s is not a valid MAC address" % self.selector["mac"].lower())
        except KeyError:
            pass

        self._target_data["selector"] = self.selector

    def generate(self):
        self._metadata()
        self._selector()
        return self.target_data
