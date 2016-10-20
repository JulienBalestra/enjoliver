import os

from generate_common import GenerateCommon


class GenerateProfile(GenerateCommon):
    def __init__(self, _id, name, ignition_id,
                 bootcfg_path=GenerateCommon.bootcfg_path):

        self.ensure_directory(bootcfg_path)
        self.ensure_directory("%s/ignition" % bootcfg_path)
        try:
            self.ensure_file("%s/ignition/%s" % (bootcfg_path, ignition_id))
        except Warning:
            os.write(2, "Warning: %s not here" % "%s/ignition/%s" % (bootcfg_path, ignition_id))

        self.target_path = self.ensure_directory("%s/profiles" % bootcfg_path)
        self._ip_address = None
        self._target_data = {
            "id": "%s" % _id,
            "name": "%s" % name,
            "boot": {},
            "cloud_id": "",
            "ignition_id": "%s" % ignition_id
        }

    def _boot(self):
        self._target_data["boot"] = {
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
        return self.target_data
