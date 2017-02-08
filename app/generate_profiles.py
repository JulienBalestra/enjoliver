from configs import EnjoliverConfig

from generate_common import GenerateCommon

ec = EnjoliverConfig()


class GenerateProfile(GenerateCommon):
    def __repr__(self):
        return "GenProfile-%s" % self._target_data["id"]

    def __init__(self,
                 api_uri,
                 _id, name,
                 ignition_id,
                 bootcfg_path):

        self.api_uri = api_uri
        self.ensure_directory(bootcfg_path)
        self.ensure_directory("%s/ignition" % bootcfg_path)
        try:
            self.ensure_file("%s/ignition/%s" % (bootcfg_path, ignition_id))
        except Warning:
            self.log.warning("not here %s/ignition/%s\n" % (bootcfg_path, ignition_id))

        self.target_path = self.ensure_directory("%s/profiles" % bootcfg_path)
        self._target_data = {
            "id": "%s" % _id,
            "name": "%s" % name,
            "boot": {},
            "cloud_id": "",
            "ignition_id": "%s" % ignition_id
        }

    def _boot(self):
        self._target_data["boot"] = {
            "kernel": "%s%s" % (self.api_uri, ec.kernel),
            "initrd": ["%s%s" % (self.api_uri, ec.initrd)],
            "cmdline": {
                "coreos.config.url":
                    "%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}" % self.api_uri,
                "coreos.autologin": "",
                "coreos.first_boot": "",
                "coreos.oem.id": "pxe"
            }
        }

    def generate(self):
        self._boot()
        self.log.info("done: %s" % self._target_data["name"])
        return self.target_data
