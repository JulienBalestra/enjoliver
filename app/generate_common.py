import json
import os
import subprocess


class GenerateCommon(object):
    app_path = "%s" % os.path.dirname(__file__)
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path

    _target_data = None
    _ip_address = None

    _raise_enof = IOError

    @property
    def target_data(self):
        if self._target_data is not None:
            return self._target_data
        return self.generate()

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
