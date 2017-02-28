import os

import yaml

app_path = os.path.dirname(os.path.abspath(__file__))
project_path = os.path.dirname(app_path)


class EnjoliverConfig(object):
    def config_override(self, key, default):
        env = "ENJOLIVER_%s" % key.upper()
        try:
            e = os.environ[env]
            print "RECOGNIZED ENV %s=%s" % (env, e)
            self.from_env[key] = e
            return e
        except KeyError:
            pass

        try:
            return self.from_yaml[key]
        except KeyError:
            self.default[key] = default
            return default

    def __init__(self, yaml_full_path=os.getenv("ENJOLIVER_CONFIGS_YAML",
                                                "%s/configs.yaml" % app_path), importer=""):
        with open(yaml_full_path) as f:
            self.from_yaml = yaml.load(f)

        self.from_env = {}
        self.default = {}

        # Flask Public endpoint
        self.api_uri = self.config_override("api_uri", None)
        # if self.api_uri is None:
        #     raise AttributeError("api_uri have to be set")
        self.gunicorn_workers = self.config_override("gunicorn_workers", 1)
        self.gunicorn_worker_type = self.config_override("gunicorn_worker_type", "sync")
        self.gunicorn_bind = self.config_override("gunicorn_bind", "0.0.0.0:5000")

        # Bootcfg aka CoreOS Baremetal aka Matchbox
        self.matchbox_uri = self.config_override("matchbox_uri", "http://127.0.0.1:8080")
        self.matchbox_path = self.config_override("matchbox_path", "%s/matchbox" % project_path)
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
        self.werkzeug_fs_cache_dir = self.config_override(
            "werkzeug_fs_cache_dir", '%s/werkzeug_cache' % os.path.dirname(
                os.path.abspath(
                    __file__)))

        # S3
        self.aws_id = self.config_override("aws_id", os.getenv("AWS_ACCESS_KEY_ID", None))
        self.aws_secret = self.config_override("aws_secret", os.getenv("AWS_SECRET_ACCESS_KEY", None))

        self.backup_lock_key = self.config_override("backup_lock_key", "backup_lock")
        self.backup_bucket_name = self.config_override("backup_bucket_name", "")
        self.backup_bucket_directory = self.config_override("backup_bucket_directory", "enjoliver")

        # Gen
        self.assets_server_uri = self.config_override("assets_server_uri", None)
        self.kernel = self.config_override("kernel",
                                           "/assets/coreos/serve/coreos_production_pxe.vmlinuz")
        self.initrd = self.config_override("initrd",
                                           "/assets/coreos/serve/coreos_production_pxe_image.cpio.gz")

        # Scheduler
        self.apply_deps_tries = int(self.config_override("apply_deps_tries", 15))
        self.apply_deps_delay = int(self.config_override("apply_deps_delay", 60))

        self.etcd_member_kubernetes_control_plane_expected_nb = int(self.config_override(
            "etcd_member_kubernetes_control_plane_expected_nb", 3))

        # Sync Matchbox
        self.sub_ips = int(self.config_override("sub_ips", 256))
        self.range_nb_ips = int(self.config_override("range_nb_ips", 253))
        self.skip_ips = int(self.config_override("skip_ips", 1))

        # Application config
        self.kubernetes_api_server_port = int(self.config_override("kubernetes_api_server_port", 8080))
        self.kubernetes_service_cluster_ip_range = self.config_override("kubernetes_service_cluster_ip_range",
                                                                        "172.30.0.0/24")

        # Kubernetes Etcd
        self.kubernetes_etcd_data_dir = self.config_override("kubernetes_etcd_data_dir", "/var/lib/etcd3/kubernetes")
        self.kubernetes_etcd_client_port = int(self.config_override("kubernetes_etcd_client_port", 2379))
        self.kubernetes_etcd_peer_port = int(self.config_override("kubernetes_etcd_peer_port", 2380))
        self.kubernetes_etcd_listen_client_urls = self.config_override(
            "kubernetes_etcd_listen_client_urls", "http://0.0.0.0:%s" % self.kubernetes_etcd_client_port)

        self.kubernetes_etcd_servers = self.config_override("kubernetes_etcd_servers",
                                                            "http://127.0.0.1:%d" % self.kubernetes_etcd_client_port)

        # Fleet Etcd
        self.fleet_etcd_data_dir = self.config_override("fleet_etcd_data_dir", "/var/lib/etcd3/fleet")
        self.fleet_etcd_client_port = int(self.config_override("fleet_etcd_client_port", 4001))
        self.fleet_etcd_peer_port = int(self.config_override("fleet_etcd_peer_port", 7001))
        self.fleet_etcd_listen_client_urls = self.config_override(
            "fleet_etcd_listen_client_urls", "http://0.0.0.0:%s" % self.fleet_etcd_client_port)

        self.fleet_etcd_servers = self.config_override("fleet_etcd_servers",
                                                       "http://127.0.0.1:%d" % self.fleet_etcd_client_port)

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

        self.coreos_install_base_url = self.config_override("coreos_install_base_url", None)

        if self.logging_level.lower() == "debug":
            os.write(2, "configs file: %s for %s\n" % (yaml_full_path, importer))


if __name__ == '__main__':
    ec = EnjoliverConfig("%s/configs.yaml" % os.path.dirname(__file__))
    for k, v in ec.__dict__.iteritems():
        if type(v) is str:
            print "%s: '%s'\n" % (k, v)
        else:
            print "%s: %s\n" % (k, v)
