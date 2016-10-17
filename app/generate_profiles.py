import json
import os
import subprocess


class GenerateProfiles(object):
    app_path = "%s" % os.path.dirname(__file__)
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path

    def __init__(self, _id, name, ignition_id):
        self._ip_address = None
        self.profile = {
            "id": "%s" % _id,
            "name": "%s" % name,
            "boot": {},
            "cloud_id": "",
            "ignition_id": "%s" % ignition_id
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

    def _boot(self):
        self.profile["boot"] = {
            "kernel": "/assets/coreos/serve/coreos_production_pxe.vmlinuz",
            "initrd": ["/assets/coreos/serve/coreos_production_pxe_image.cpio.gz"],
            "cmdline": {
                "coreos.config.url":
                    "http://%s:8080/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}" % self.ip_address,
                "coreos.autologin": "",
                "coreos.first_boot": ""
            }
        }

    def generate(self):
        self._boot()
        return self.profile

    def render(self, indent=4):
        self.generate()
        return json.dumps(self.profile, indent=indent)
