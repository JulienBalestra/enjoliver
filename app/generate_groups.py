import re

from generate_common import GenerateCommon


class GenerateGroup(GenerateCommon):
    def __repr__(self):
        return "GenGroup[%s]" % self._target_data["id"]

    def __init__(self, _id, name, profile, selector=None, metadata=None,
                 bootcfg_path=GenerateCommon.bootcfg_path):

        self.ensure_directory(bootcfg_path)
        self.target_path = self.ensure_directory("%s/groups" % bootcfg_path)
        self.extra_selector = None if not selector else dict(selector)
        self.extra_metadata = {} if not metadata else dict(metadata)

        self._target_data = {
            "id": _id,
            "name": name,
            "profile": profile,
            "metadata": {
                "api_uri": "",
                "bootcfg_uri": "",
                "etcd_initial_cluster": ""
            }
        }

    def _metadata(self):
        self._target_data["metadata"]["api_uri"] = self.api_uri
        self._target_data["metadata"]["bootcfg_uri"] = self.bootcfg_uri
        self._target_data["metadata"]["etcd_initial_cluster"] = ""  # default WET

        for k, v in self.extra_metadata.iteritems():
            self.log_stderr("add %s: %s in metadata" % (k, v))
            self._target_data["metadata"][k] = v

    def _selector(self):
        if self.extra_selector is None:
            return

        if type(self.extra_selector) is not dict:
            raise TypeError("selector is not a dict")

        try:
            self.extra_selector["mac"] = self.extra_selector["mac"].lower()
            match = re.match(r"^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$",
                             self.extra_selector["mac"])
            if match is None:
                raise TypeError("%s is not a valid MAC address" % self.extra_selector["mac"].lower())
        except KeyError:
            pass

        self._target_data["selector"] = self.extra_selector
        self._target_data["metadata"]["selector"] = self.extra_selector

    def generate(self):
        self._metadata()
        self._selector()
        self.log_stderr("generate")
        return self.target_data
