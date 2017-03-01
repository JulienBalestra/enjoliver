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


class TestKVMK8sEnjolivage(kvm_player.KernelVirtualMachinePlayer):
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
            api_uri=self.api_uri)

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
                    "--memory=%d" % self.get_optimized_memory(nb_node),
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

            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

            for i in range(60):
                if plan_k8s_2t.apply() == 1:
                    break
                time.sleep(self.testing_sleep_seconds)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

            self.etcd_endpoint_health(plan_k8s_2t.etcd_member_ip_list, self.ec.kubernetes_etcd_client_port)
            self.etcd_endpoint_health(plan_k8s_2t.etcd_member_ip_list, self.ec.fleet_etcd_client_port)
            self.k8s_api_health(plan_k8s_2t.kubernetes_control_plane_ip_list)
            self.etcd_member_k8s_minions(plan_k8s_2t.etcd_member_ip_list[0], nb_node)

            self.create_nginx_daemon_set(plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            self.create_nginx_deploy(plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            ips = copy.deepcopy(plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list)
            self.daemon_set_nginx_are_running(ips)
            self.pod_nginx_is_running(plan_k8s_2t.kubernetes_control_plane_ip_list[0])

            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage(
                    api_server_uri="http://%s:8080" % plan_k8s_2t.kubernetes_control_plane_ip_list[0])
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy)
                self.virsh(undefine)


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
