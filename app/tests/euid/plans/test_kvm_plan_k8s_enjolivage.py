import copy
import os
import sys
import time
import unittest

from app.plans import enjolivage

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
        cls.set_bootcfg()
        cls.set_dnsmasq()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("")
class TestKVMK8sEnjolivage0(TestKVMK8sEnjolivage):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 4
        marker = "plans-%s-%s" % (TestKVMK8sEnjolivage.__name__.lower(), self.test_00.__name__)
        nodes = ["%s-%d" % (marker, i) for i in xrange(nb_node)]
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"

        plan_enjolivage = enjolivage.Enjolivage(marker,
                                                bootcfg_path=self.test_bootcfg_path,
                                                api_uri="http://127.0.0.1:5000")

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
                    "--memory=%d" % (self.get_optimized_memory() // 2),
                    "--vcpus=2",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)

            time.sleep(self.kvm_sleep_between_node * self.kvm_sleep_between_node)

            for i in range(60):
                if plan_enjolivage.run() == 1:
                    break
                time.sleep(self.kvm_sleep_between_node)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.kvm_sleep_between_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(plan_enjolivage.etcd_member_k8s_control_plane.ip_list)
            self.k8s_api_health(plan_enjolivage.etcd_member_k8s_control_plane.ip_list)
            self.etcd_member_k8s_minions(plan_enjolivage.etcd_member_k8s_control_plane.ip_list[0], nb_node)

            self.create_nginx_daemon_set(plan_enjolivage.etcd_member_k8s_control_plane.ip_list[0])
            self.create_nginx_deploy(plan_enjolivage.etcd_member_k8s_control_plane.ip_list[0])
            ips = copy.deepcopy(
                plan_enjolivage.k8s_node.ip_list + plan_enjolivage.etcd_member_k8s_control_plane.ip_list)
            self.daemon_set_nginx_are_running(ips)
            self.pod_nginx_is_running(plan_enjolivage.etcd_member_k8s_control_plane.ip_list[0])

            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage(
                    api_server_uri="http://%s:8080" % plan_enjolivage.etcd_member_k8s_control_plane.ip_list[0])
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
