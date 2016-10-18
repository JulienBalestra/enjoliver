import json
import os
import subprocess


class GenerateGroup(object):
    app_path = "%s" % os.path.dirname(__file__)
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path
    profiles_path = "%s/groups" % bootcfg_path

    def __init__(self, _id, name, profile):
        self._ip_address = None
        self.group = {
            "id": _id,
            "name": name,
            "profile": profile,
            "metadata": {
                "seed": "",
                "etcd_initial_cluster": ""
            }
        }

    @property
    def ip_address(self):
        if self._ip_address:
            return self._ip_address
        out = "%s/misc/network-environment" % self.bootcfg_path
        subprocess.check_call(
            ["%s/assets/setup-network-environment/serve/setup-network-environment" % self.bootcfg_path,
             "-o", "%s" % out])
        with open("%s" % out, mode='r') as fd:
            for l in fd:
                if "DEFAULT_IPV4=" in l:
                    self._ip_address = l.split("DEFAULT_IPV4=")[1].replace("\n", "")
                    return self._ip_address
        raise ImportError("Error in module %s" % out)

    def _metadata(self):
        self.group["metadata"]["seed"] = "http://%s:8080" % self.ip_address
        self.group["metadata"]["etcd_initial_cluster"] = ""

    def generate(self):
        self._metadata()
        return self.group

    def render(self, indent=4):
        self.generate()
        return json.dumps(self.group, indent=indent)

    def dump(self):
        with open("%s/%s.json" % (self.profiles_path, self.group["id"]), "w") as fd:
            fd.write(self.render())
