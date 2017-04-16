import copy
import sys
import unittest

import os
import time

from app import generator, schedulerv2, sync

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


class TestKVMK8sFast(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_acserver()
        cls.set_rack0()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("")
class TestKVMK8SFast0(TestKVMK8sFast):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMK8sFast.__name__.lower(), self.test_00.__name__)
        nodes = ["%s-%d" % (marker, i) for i in range(nb_node)]
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path
        )
        gen.dumps()
        sy = sync.ConfigSyncSchedules(
            api_uri=self.api_uri,
            matchbox_path=self.test_matchbox_path,
            ignition_dict={
                "etcd_member_kubernetes_control_plane": "%s-%s" % (marker, "k8s-control-plane"),
                "kubernetes_nodes": "%s-%s" % (marker, "k8s-node")
            }
        )
        for m in nodes:
            destroy, undefine = ["virsh", "destroy", m], \
                                ["virsh", "undefine", m]
            self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            for i, m in enumerate(nodes):
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=%d" % self.ram_kvm_node_memory_mb,
                    "--vcpus=%d" % self.get_optimized_cpu(nb_node),
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)

            sch_cp = schedulerv2.EtcdMemberKubernetesControlPlane(self.api_uri)
            sch_cp.expected_nb = 1
            for i in range(60):
                if sch_cp.apply() is True:
                    sy.apply()
                    break
                time.sleep(self.testing_sleep_seconds)

            self.assertTrue(sch_cp.apply())
            sch_no = schedulerv2.KubernetesNode(self.api_uri, apply_dep=False)
            for i in range(60):
                if sch_no.apply() == nb_node - sch_cp.expected_nb:
                    break
                time.sleep(self.testing_sleep_seconds)
            self.assertEqual(nb_node - sch_cp.expected_nb, sch_no.apply())
            sy.apply()

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.testing_sleep_seconds * nb_node)

            self.etcd_member_len(sy.kubernetes_control_plane_ip_list[0], sch_cp.expected_nb,
                                 self.ec.vault_etcd_client_port, verify=False)
            self.etcd_endpoint_health(sy.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port, verify=False)

            self.vault_self_certs(sy.kubernetes_control_plane_ip_list[0], self.ec.vault_etcd_client_port)
            self.vault_verifing_issuing_ca(sy.kubernetes_control_plane_ip_list[0], self.ec.vault_etcd_client_port)
            self.vault_issue_app_certs(sy.kubernetes_control_plane_ip_list[0], self.ec.vault_etcd_client_port)

            self.save_unseal_key(sy.kubernetes_control_plane_ip_list)
            self.unseal_all_vaults(sy.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port)

            self.etcd_member_len(sy.kubernetes_control_plane_ip_list[0], sch_cp.expected_nb,
                                 self.ec.kubernetes_etcd_client_port, certs_name="etcd-kubernetes_client")
            self.etcd_member_len(sy.kubernetes_control_plane_ip_list[0], sch_cp.expected_nb,
                                 self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

            self.etcd_endpoint_health(sy.kubernetes_control_plane_ip_list, self.ec.kubernetes_etcd_client_port,
                                      certs_name="etcd-kubernetes_client")
            self.etcd_endpoint_health(sy.kubernetes_control_plane_ip_list + sy.kubernetes_nodes_ip_list,
                                      self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")
            self.k8s_api_health(sy.kubernetes_control_plane_ip_list)
            self.k8s_node_nb(sy.kubernetes_control_plane_ip_list[0], nb_node)
            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage(
                    api_server_uri="http://%s:8080" % sy.kubernetes_control_plane_ip_list[0],
                    # fns=[sch_cp.apply, sch_no.apply, sy.apply]
                )
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy)
                self.virsh(undefine)


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
