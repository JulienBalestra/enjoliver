import json
import os
import subprocess


class GenerateCommon(object):
    app_path = "%s" % os.path.dirname(__file__)
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path

    target_data = {
        "id": "",
        "name": ""
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

    def generate(self):
        raise NotImplementedError

    def render(self, indent=4):
        self.generate()
        return json.dumps(self.target_data, indent=indent)

    def dump(self):
        with open("%s/%s.json" % (self.target_path, self.target_data["id"]), "w") as fd:
            fd.write(self.render())
