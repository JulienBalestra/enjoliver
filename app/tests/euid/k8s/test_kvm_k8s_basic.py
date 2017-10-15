import copy
import os
import unittest

import sys
import time

from app.plans import k8s_2t

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


class TestKVMK8sBasic(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.running_requirements()
        cls.set_rack0()
        cls.set_acserver()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("skip")
class TestKVMK8SBasic0(TestKVMK8sBasic):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery(), [])
        nb_node = 2
        marker = "euid-%s-%s" % (TestKVMK8sBasic.__name__.lower(), self.test_00.__name__)
        nodes = ["%s-%d" % (marker, i) for i in range(nb_node)]
        plan_k8s_2t = k8s_2t.Kubernetes2Tiers(
            {
                "discovery": marker,
                "etcd_member_kubernetes_control_plane": "%s-%s" % (marker, "etcd-member-control-plane"),
                "kubernetes_nodes": "%s-%s" % (marker, "k8s-node"),
            },
            matchbox_path=self.test_matchbox_path,
            api_uri=self.api_uri,
            extra_selectors=dict(),
        )
        plan_k8s_2t._sch_k8s_control_plane.expected_nb = 1

        try:
            for i, m in enumerate(nodes):
                # if the machine already exist: clean it
                self.clean_up_virtual_machine(m)
                virt_install = self.create_virtual_machine(m, nb_node)
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)

            for i in range(120):
                if plan_k8s_2t.apply() == nb_node:
                    break
                time.sleep(self.testing_sleep_seconds)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.testing_sleep_seconds * nb_node)

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
                                 plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                                 self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

            self.etcd_endpoint_health(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.kubernetes_etcd_client_port,
                                      certs_name="etcd-kubernetes_client")
            self.etcd_endpoint_health(
                plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list,
                self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")
            self.kube_apiserver_health(plan_k8s_2t.kubernetes_control_plane_ip_list)
            self.create_tiller(plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            self.kubernetes_node_nb(plan_k8s_2t.kubernetes_control_plane_ip_list[0], nb_node)
            self.healthz_enjoliver_agent(
                plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list)

            self.pod_tiller_is_running(plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            for chart in ["heapster", "node-exporter", "prometheus"]:
                self.create_helm_by_name(plan_k8s_2t.kubernetes_control_plane_ip_list[0], chart)

            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage(
                    api_server_ip=plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                )
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                self.clean_up_virtual_machine(machine_marker)


# @unittest.skip("")
class TestKVMK8SBasic1(TestKVMK8sBasic):
    # @unittest.skip("just skip")
    def test_01(self):
        self.assertEqual(self.fetch_discovery(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMK8sBasic.__name__.lower(), self.test_01.__name__)
        nodes = ["%s-%d" % (marker, i) for i in range(nb_node)]
        plan_k8s_2t = k8s_2t.Kubernetes2Tiers(
            {
                "discovery": marker,
                "etcd_member_kubernetes_control_plane": "%s-%s" % (marker, "etcd-member-control-plane"),
                "kubernetes_nodes": "%s-%s" % (marker, "k8s-node"),
            },
            matchbox_path=self.test_matchbox_path,
            api_uri=self.api_uri,
            extra_selectors=dict(),
        )
        plan_k8s_2t._sch_k8s_control_plane.expected_nb = 3

        try:
            for i, m in enumerate(nodes):
                # if the machine already exist: clean it
                self.clean_up_virtual_machine(m)
                virt_install = self.create_virtual_machine(m, nb_node)
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)

            for i in range(120):
                if plan_k8s_2t.apply() == nb_node:
                    break
                time.sleep(self.testing_sleep_seconds)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.testing_sleep_seconds * nb_node)

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
                                 plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                                 self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

            self.etcd_endpoint_health(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.kubernetes_etcd_client_port,
                                      certs_name="etcd-kubernetes_client")
            self.etcd_endpoint_health(
                plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list,
                self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")
            self.kube_apiserver_health(plan_k8s_2t.kubernetes_control_plane_ip_list)
            self.create_tiller(plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            self.kubernetes_node_nb(plan_k8s_2t.kubernetes_control_plane_ip_list[0], nb_node)

            self.pod_tiller_is_running(plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            for chart in ["heapster", "node-exporter", "prometheus"]:
                self.create_helm_by_name(plan_k8s_2t.kubernetes_control_plane_ip_list[0], chart)

            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage(
                    api_server_ip=plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                )
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                self.clean_up_virtual_machine(machine_marker)


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
