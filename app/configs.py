import os


class EnjoliverConfig(object):
    def __init__(self):
        # Flask Public endpoint
        self.api_uri = os.getenv("API_URI", None)

        # Bootcfg aka CoreOS Baremetal aka Matchbox
        self.bootcfg_uri = "http://127.0.0.1:8080"

        # Databases
        self.db_path = os.getenv("DB_PATH", '%s/enjoliver.sqlite' % os.path.dirname(os.path.abspath(__file__)))
        self.db_uri = 'sqlite:///%s' % self.db_path
        self.ignition_journal_dir = os.getenv("IGNITION_JOURNAL_DIR",
                                              '%s/ignition_journal' % os.path.dirname(os.path.abspath(__file__)))

        # S3
        self.aws_id = os.getenv("AWS_ACCESS_KEY_ID", None)
        self.aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", None)

        self.backup_backup_name = os.getenv("BACKUP_BUCKET_NAME", "")
        self.backup_backup_directory = os.getenv("BACKUP_BUCKET_DIRECTORY", "enjoliver")

        # Gen
        self.kernel = "/assets/coreos/serve/coreos_production_pxe.vmlinuz"
        self.initrd = "/assets/coreos/serve/coreos_production_pxe_image.cpio.gz"

        # Scheduler
        self.apply_deps_tries = 15
        self.apply_deps_delay = 60

        self.etcd_member_kubernetes_control_plane_expected_nb = 3

        # Sync Bootcfg
        self.ipam_multiplier = 256
        self.ipam_ips = 254

        # Application config
        self.kubernetes_api_server_port = 8080

        self.etcd_initial_advertise_peer_port = 2380
        self.etcd_advertise_client_port = 2379
