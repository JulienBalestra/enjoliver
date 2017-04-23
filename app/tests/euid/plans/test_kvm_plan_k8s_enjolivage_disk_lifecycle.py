import copy
import os
import sys
import time
import unittest

from app.plans import k8s_2t

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


@unittest.skipIf(os.getenv("DISK_OK") is None, "Skip because DISK_OK=")
class TestKVMK8sEnjolivageDiskLifecycle(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_rack0()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.set_acserver()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("")
class TestKVMK8SEnjolivageDiskLifecycleLifecycle0(TestKVMK8sEnjolivageDiskLifecycle):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "plans-%s-%s" % (TestKVMK8sEnjolivageDiskLifecycle.__name__.lower(), self.test_00.__name__)
        nodes = ["%s-%d" % (marker, i) for i in range(nb_node)]
        plan_k8s_2t = k8s_2t.Kubernetes2Tiers(
            {
                "discovery": marker,
                "etcd_member_kubernetes_control_plane": "%s-%s" % (marker, "etcd-member-control-plane"),
                "kubernetes_nodes": "%s-%s" % (marker, "k8s-node"),
            },
            matchbox_path=self.test_matchbox_path,
            api_uri=self.api_uri,
            extra_selectors=self.ec.extra_selectors,
        )

        for i in range(nb_node):
            machine_marker = "%s-%d" % (marker, i)
            destroy, undefine, vol_delete = ["virsh", "destroy", "%s" % machine_marker], \
                                            ["virsh", "undefine", "%s" % machine_marker], \
                                            ["virsh", "vol-delete", "%s.qcow2" % machine_marker, "--pool",
                                             "default"]
            self.virsh(destroy)
            self.virsh(undefine)
            self.virsh(vol_delete)
        try:
            for i, m in enumerate(nodes):
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=%d" % self.get_optimized_memory(nb_node),
                    "--vcpus=%d" % self.get_optimized_cpu(nb_node),
                    "--pxe",
                    "--disk",
                    "size=10",  # HERE State machine
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=hd,network",  # Boot on disk if here
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)

            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

            for i in range(120):
                if plan_k8s_2t.apply() == 0:
                    break
                time.sleep(self.testing_sleep_seconds)

            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds + (nb_node * 10))

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            for i in range(nb_node * 3 + 1):
                time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

                self.etcd_member_len(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                     plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                                     self.ec.vault_etcd_client_port, tries=60, verify=False)
                self.etcd_endpoint_health(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port,
                                          verify=False, tries=60)

                if i == 0:
                    self.vault_self_certs(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                          self.ec.vault_etcd_client_port)
                    self.vault_verifing_issuing_ca(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                                   self.ec.vault_etcd_client_port)
                    self.vault_issue_app_certs(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                               self.ec.vault_etcd_client_port)
                    self.save_unseal_key(plan_k8s_2t.kubernetes_control_plane_ip_list)

                self.unseal_all_vaults(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port)

                self.etcd_member_len(
                    plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3], plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                    self.ec.kubernetes_etcd_client_port, certs_name="etcd-kubernetes_client")
                self.etcd_member_len(
                    plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3], plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                    self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

                self.etcd_endpoint_health(
                    plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.kubernetes_etcd_client_port,
                    certs_name="etcd-kubernetes_client")
                self.etcd_endpoint_health(
                    plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list,
                    self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

                self.kube_apiserver_health(plan_k8s_2t.kubernetes_control_plane_ip_list)
                self.kubernetes_node_nb(plan_k8s_2t.etcd_member_ip_list[i % 3], nb_node)

                if i == 0:
                    self.create_httpd_daemon_set(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3])
                    self.create_httpd_deploy(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3])
                    self.create_tiller_deploy(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3])

                ips = copy.deepcopy(plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list)
                self.daemon_set_httpd_are_running(ips)
                self.pod_httpd_is_running(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3])
                self.pod_tiller_is_running(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3])

                for etcd in ["vault", "kubernetes"]:
                    if i == 0:
                        self.create_helm_etcd_backup(plan_k8s_2t.etcd_member_ip_list[i % 3], etcd)
                    self.etcd_backup_done(plan_k8s_2t.etcd_member_ip_list[i % 3], etcd)

                machine_marker = "%s-%d" % (marker, i % 3)
                destroy, vol_delete, vol_create, start = \
                    ["virsh", "destroy", "%s" % machine_marker], \
                    ["virsh", "vol-delete", "%s.qcow2" % machine_marker, "--pool", "default"], \
                    ["virsh", "vol-create-as", "--name", "%s.qcow2" % machine_marker,
                     "--pool", "default", "--capacity", "11GB", "--format", "qcow2"], \
                    ["virsh", "start", "%s" % machine_marker]

                self.virsh(destroy)
                time.sleep(1)
                if i + 1 > nb_node * 2:
                    self.virsh(vol_delete)
                    self.virsh(vol_create)
                self.virsh(start)

            self.write_ending(marker)

        finally:
            try:
                if os.getenv("TEST"):
                    self.iteractive_usage(
                        api_server_uri="http://%s:8080" % plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                        # fns=[plan_k8s_2t.apply]
                    )
            finally:
                for i in range(nb_node):
                    machine_marker = "%s-%d" % (marker, i)
                    destroy, undefine, vol_del = ["virsh", "destroy", "%s" % machine_marker], \
                                                 ["virsh", "undefine", "%s" % machine_marker], \
                                                 ["virsh", "vol-delete", "%s.qcow2" % machine_marker, "--pool",
                                                  "default"]
                    self.virsh(destroy)
                    self.virsh(undefine)
                    self.virsh(vol_del)


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
