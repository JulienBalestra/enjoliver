import unittest

import copy
import os
import sys
import time

from app.plans import k8s_2t

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


class TestKVMK8sEnjolivage(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.running_requirements()
        cls.set_rack0()
        cls.set_acserver()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("")
class TestKVMK8sEnjolivage0(TestKVMK8sEnjolivage):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 4
        marker = "plans-%s-%s" % (TestKVMK8sEnjolivage.__name__.lower(), self.test_00.__name__)
        nodes = ["%s-%d" % (marker, i) for i in range(nb_node)]
        plan_k8s_2t = k8s_2t.Kubernetes2Tiers(
            {
                "discovery": marker,
                "etcd_member_kubernetes_control_plane": "%s-%s" % (marker, "etcd-member-control-plane"),
                "kubernetes_nodes": "%s-%s" % (marker, "k8s-node"),
            },
            matchbox_path=self.test_matchbox_path,
            api_uri=self.api_uri,
        )

        for m in nodes:
            destroy, undefine = ["virsh", "destroy", m], \
                                ["virsh", "undefine", m]
            self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            for i, m in enumerate(nodes):
                virt_install = self.create_virtual_machine(m, nb_node)
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)

            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

            for i in range(60):
                if plan_k8s_2t.apply() == 1:
                    break
                time.sleep(self.testing_sleep_seconds)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

            self.etcd_member_len(plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                                 plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                                 self.ec.vault_etcd_client_port, verify=False)
            self.etcd_endpoint_health(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port,
                                      verify=False)

            self.vault_self_certs(plan_k8s_2t.kubernetes_control_plane_ip_list[0], self.ec.vault_etcd_client_port)
            self.vault_verifing_issuing_ca(plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                                           self.ec.vault_etcd_client_port)
            self.vault_issue_app_certs(plan_k8s_2t.kubernetes_control_plane_ip_list[0], self.ec.vault_etcd_client_port)

            self.save_unseal_key(plan_k8s_2t.kubernetes_control_plane_ip_list)
            self.unseal_all_vaults(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port)

            self.etcd_member_len(plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                                 plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                                 self.ec.kubernetes_etcd_client_port, certs_name="etcd-kubernetes_client")
            self.etcd_member_len(plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                                 plan_k8s_2t._sch_k8s_control_plane.expected_nb, self.ec.fleet_etcd_client_port,
                                 certs_name="etcd-fleet_client")

            self.etcd_endpoint_health(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.kubernetes_etcd_client_port,
                                      certs_name="etcd-kubernetes_client")
            self.etcd_endpoint_health(
                plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list,
                self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

            self.kube_apiserver_health(plan_k8s_2t.kubernetes_control_plane_ip_list)
            self.kubernetes_node_nb(plan_k8s_2t.etcd_member_ip_list[0], nb_node)

            self.create_tiller(plan_k8s_2t.etcd_member_ip_list[0])
            self.pod_tiller_is_running(plan_k8s_2t.etcd_member_ip_list[0])

            for etcd in ["vault", "kubernetes"]:
                self.create_helm_etcd_backup(plan_k8s_2t.etcd_member_ip_list[0], etcd)

            for chart in ["heapster", "node-exporter", "prometheus"]:
                self.create_helm_by_name(plan_k8s_2t.etcd_member_ip_list[0], chart)

            # Resilient testing against rktnetes
            # See https://github.com/kubernetes/kubernetes/issues/45149
            self.tiller_can_restart(plan_k8s_2t.kubernetes_control_plane_ip_list[0])

            # takes about one minute to run the cronjob
            for etcd in ["vault", "kubernetes"]:
                self.etcd_backup_done(plan_k8s_2t.etcd_member_ip_list[0], etcd)
            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage(
                    api_server_uri="https://%s:6443" % plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy)
                self.virsh(undefine)


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
