import os

import yaml


class EnjoliverConfig(object):
    def config_override(self, key, default):
        try:
            env = "ENJOLIVER_%s" % key.upper()
            e = os.getenv(env, None)
            if e is not None:
                print "RECOGNIZED ENV %s=%s" % (env, e)
                return e
            if not self.c[key]:
                raise KeyError
            return self.c[key]
        except KeyError:
            return default

    def __init__(self, yaml_full_path="%s/configs.yaml" % os.path.dirname(__file__)):
        try:
            with open(yaml_full_path) as f:
                self.c = yaml.load(f)
        except IOError:
            with open(yaml_full_path.replace(".yaml", ".yml")) as f:
                self.c = yaml.load(f)

        # Flask Public endpoint
        self.api_uri = self.config_override("api_uri", None)
        # if self.api_uri is None:
        #     raise AttributeError("api_uri have to be set")
        self.gunicorn_workers = self.config_override("gunicorn_workers", 1)

        # Bootcfg aka CoreOS Baremetal aka Matchbox
        self.matchbox_uri = self.config_override("matchbox_uri", "http://127.0.0.1:8080")
        self.matchbox_path = self.config_override("matchbox_path", "/var/lib/matchbox")
        self.matchbox_assets = self.config_override("matchbox_assets", "%s/assets" % self.matchbox_path)
        # For Health check
        self.matchbox_urls = self.config_override("matchbox_urls", [
            "/",
            "/boot.ipxe",
            "/boot.ipxe.0",
            "/assets",
            "/metadata"
        ])

        # Databases
        self.db_path = self.config_override("db_path", '%s/enjoliver.sqlite' % os.path.dirname(
            os.path.abspath(__file__)))
        self.db_uri = self.config_override("db_uri", 'sqlite:///%s' % self.db_path)
        self.ignition_journal_dir = self.config_override(
            "ignition_journal_dir", '%s/ignition_journal' % os.path.dirname(
                os.path.abspath(
                    __file__)))

        # S3
        self.aws_id = self.config_override("aws_id", os.getenv("AWS_ACCESS_KEY_ID", None))
        self.aws_secret = self.config_override("aws_secret", os.getenv("AWS_SECRET_ACCESS_KEY", None))

        self.backup_lock_key = self.config_override("backup_lock_key", "backup_lock")
        self.backup_bucket_name = self.config_override("backup_bucket_name", "")
        self.backup_bucket_directory = self.config_override("backup_bucket_directory", "enjoliver")

        # Gen
        self.kernel = self.config_override("kernel", "/assets/coreos/serve/coreos_production_pxe.vmlinuz")
        self.initrd = self.config_override("initrd", "/assets/coreos/serve/coreos_production_pxe_image.cpio.gz")

        # Scheduler
        self.apply_deps_tries = self.config_override("apply_deps_tries", 15)
        self.apply_deps_delay = self.config_override("apply_deps_delay", 60)

        self.etcd_member_kubernetes_control_plane_expected_nb = self.config_override(
            "etcd_member_kubernetes_control_plane_expected_nb", 3)

        # Sync Matchbox
        self.sub_ips = self.config_override("sub_ips", 256)
        self.range_nb_ips = self.config_override("range_nb_ips", 253)
        self.skip_ips = self.config_override("skip_ips", 1)

        # Application config
        self.kubernetes_api_server_port = self.config_override("kubernetes_api_server_port", 8080)
        self.kubernetes_service_cluster_ip_range = self.config_override("kubernetes_service_cluster_ip_range",
                                                                        "172.30.0.0/24")

        self.etcd_initial_advertise_peer_port = self.config_override("etcd_initial_advertise_peer_port", 2380)
        self.etcd_advertise_client_port = self.config_override("etcd_advertise_client_port", 2379)
        self.etcd_data_dir = self.config_override("etcd_data_dir", "/var/lib/etcd3")

        # Use a real registry in production like:
        # enjoliver.local/hyperkube:latest
        self.lldp_image_url = self.config_override("lldp_image_url", "enjoliver.local/lldp:latest")
        self.hyperkube_image_url = self.config_override("hyperkube_image_url", "enjoliver.local/hyperkube:latest")

        # Ignition
        # All of them have to be in the matchbox/ignition
        # Specify only the title of the file without the extension (.yaml)
        self.ignition_dict = self.config_override("ignition_dict", {
            "discovery": "discovery",
            "etcd_member_kubernetes_control_plane": "etcd-member-control-plane",
            "kubernetes_nodes": "k8s-node",
        })

        self.extra_selectors = self.config_override("extra_selectors", {"os": "installed"})

        # Logging level
        # DEBUG or INFO
        self.logging_level = self.config_override("logging_level", "DEBUG")

        self.etc_hosts = self.config_override("etc_hosts", [
            "172.20.0.1 enjoliver.local",
        ])

        # PID files
        self.matchbox_pid_file = self.config_override("matchbox_pid_file",
                                                      "%s/matchbox.pid" % os.path.dirname(__file__))
        self.gunicorn_pid_file = self.config_override("gunicorn_pid_file",
                                                      "%s/gunicorn.pid" % os.path.dirname(__file__))
        self.plan_pid_file = self.config_override("plan_pid_file", "%s/plan.pid" % os.path.dirname(__file__))


if __name__ == '__main__':
    ec = EnjoliverConfig("%s/configs.yaml" % os.path.dirname(__file__))
    print yaml.dump(ec)
