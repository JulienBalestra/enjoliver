import os
import subprocess

base = {
    "id": "etcd-proxy",
    "name": "etcd-proxy",
    "boot": {
        "kernel": "/assets/coreos/serve/coreos_production_pxe.vmlinuz",
        "initrd": ["/assets/coreos/serve/coreos_production_pxe_image.cpio.gz"],
        "cmdline": {
            "coreos.config.url": "http://localhost:8080/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}",
            "coreos.autologin": "",
            "coreos.first_boot": ""
        }
    },
    "cloud_id": "",
    "ignition_id": "etcd.yaml"
}


class GenerateProfiles(object):
    app_path = "%s" % os.path.dirname(__file__)
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path

    def __init__(self):
        print self.project_path
        self._ip_address = None
        self.profile = {}

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

    def boot(self):
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


if __name__ == "__main__":
    gen = GenerateProfiles()
    gen.boot()
