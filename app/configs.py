"""
Configuration loading and storing inside EnjoliverConfig class
"""
import os

import yaml

APP_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(APP_PATH)


class EnjoliverConfig(object):
    """
    Used to propagate easily the configuration inside the application
    """

    def config_override(self, key: str, default):
        """
        Each config attribute pass inside this method to allow override by
        1) Environment
        2) Yaml
        And finally use the default passed in argument
        :param key:
        :param default:
        :return:
        """
        env = "ENJOLIVER_%s" % key.upper()
        try:
            env_var = os.environ[env]
            print("RECOGNIZED ENV %s=%s" % (env, env_var))
            self.from_env[key] = env_var
            return env_var
        except KeyError:
            pass

        try:
            return self.from_yaml[key]
        except KeyError:
            self.default[key] = default
            return default

    def __init__(self, yaml_full_path=os.getenv("ENJOLIVER_CONFIGS_YAML",
                                                "%s/configs.yaml" % APP_PATH), importer=""):
        with open(yaml_full_path) as yaml_fd:
            self.from_yaml = yaml.load(yaml_fd)

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
        self.matchbox_path = self.config_override("matchbox_path", "%s/matchbox" % PROJECT_PATH)
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
        self.kubernetes_apiserver_insecure_bind_address = self.config_override(
            "kubernetes_apiserver_insecure_bind_address", "127.0.0.1")

        # Kubernetes Etcd
        self.kubernetes_etcd_data_dir = self.config_override("kubernetes_etcd_data_dir", "/var/lib/etcd3/kubernetes")
        self.kubernetes_etcd_client_port = int(self.config_override("kubernetes_etcd_client_port", 2379))
        self.kubernetes_etcd_peer_port = int(self.config_override("kubernetes_etcd_peer_port", 2380))

        # Fleet Etcd
        self.fleet_etcd_data_dir = self.config_override("fleet_etcd_data_dir", "/var/lib/etcd3/fleet")
        self.fleet_etcd_client_port = int(self.config_override("fleet_etcd_client_port", 4001))
        self.fleet_etcd_peer_port = int(self.config_override("fleet_etcd_peer_port", 7001))

        # Vault Etcd
        self.vault_etcd_data_dir = self.config_override("vault_etcd_data_dir", "/var/lib/etcd3/vault")
        self.vault_etcd_client_port = int(self.config_override("vault_etcd_client_port", 4001))
        self.vault_etcd_peer_port = int(self.config_override("vault_etcd_peer_port", 7001))

        # Use a real registry in production like:
        # enjoliver.local/hyperkube:latest
        self.lldp_image_url = self.config_override("lldp_image_url", "enjoliver.local/lldp:latest")
        self.hyperkube_image_url = self.config_override("hyperkube_image_url", "enjoliver.local/hyperkube:1.6.6")
        self.rkt_image_url = self.config_override("rkt_image_url", "enjoliver.local/rkt:1.27.0")
        self.etcd_image_url = self.config_override("etcd_image_url", "enjoliver.local/etcd:3.2.0")
        self.fleet_image_url = self.config_override("fleet_image_url", "enjoliver.local/fleet:1.0.0")
        self.cni_image_url = self.config_override("cni_image_url", "enjoliver.local/cni:0.5.2")
        self.vault_image_url = self.config_override("vault_image_url", 'enjoliver.local/vault:0.7.0')

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

        self.matchbox_logging_level = self.config_override("matchbox_logging_level", "debug")
        allowed = ["debug", "info", "warning", "error"]
        if self.matchbox_logging_level not in allowed:
            raise AttributeError("%s not in [%s]" % (self.matchbox_logging_level, " ".join(allowed)))

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
        self.coreos_install_lock_seconds = self.config_override("coreos_install_lock_seconds", 29)

        self.nameservers = self.config_override("nameservers", ["8.8.8.8", "8.8.4.4"])
        self.ntp = self.config_override("ntp", ["0.arch.pool.ntp.org",
                                                "1.arch.pool.ntp.org" "2.arch.pool.ntp.org" "3.arch.pool.ntp.org"])
        self.fallbackntp = self.config_override("fallbackntp", ["0.pool.ntp.org" "1.pool.ntp.org" "0.fr.pool.ntp.org"])

        self.vault_polling_sec = self.config_override("vault_polling_sec", 30)
        self.lifecycle_update_polling_sec = self.config_override("lifecycle_update_polling_sec", 30)

        if self.logging_level.lower() == "debug":
            print("configs file: %s for %s" % (yaml_full_path, importer))


if __name__ == '__main__':
    EC = EnjoliverConfig("%s/configs.yaml" % os.path.dirname(__file__))
    for k, v in EC.__dict__.items():
        if isinstance(v, str):
            print("%s: '%s'" % (k, v))
        else:
            print("%s: %s" % (k, v))
