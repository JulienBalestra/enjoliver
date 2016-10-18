from generate_common import GenerateCommon


class GenerateGroup(GenerateCommon):
    def __init__(self, _id, name, profile,
                 bootcfg_path=GenerateCommon.bootcfg_path):
        self.target_path = "%s/groups" % bootcfg_path

        self._ip_address = None
        self.target_data = {
            "id": _id,
            "name": name,
            "profile": profile,
            "metadata": {
                "seed": "",
                "etcd_initial_cluster": ""
            }
        }

    def _metadata(self):
        self.target_data["metadata"]["seed"] = "http://%s:8080" % self.ip_address
        self.target_data["metadata"]["etcd_initial_cluster"] = ""

    def generate(self):
        self._metadata()
        return self.target_data
