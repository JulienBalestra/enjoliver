import copy
import os
import sys
import time
import unittest

from app.plans import all_in_one

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


class TestKVMK8sBasic(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_rack0()
        cls.set_api()
        cls.set_bootcfg()
        cls.set_dnsmasq()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("skip")
class TestKVMAllInOne(TestKVMK8sBasic):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        marker = "plans-%s-%s" % (TestKVMAllInOne.__name__.lower(), self.test_00.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        os.environ["BOOTCFG_PATH"] = self.test_bootcfg_path
        all_in_one.all_in_one(marker)
        destroy, undefine = ["virsh", "destroy", marker], \
                            ["virsh", "undefine", marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
                "--network=bridge:rack0,model=virtio",
                "--memory=10240",
                "--vcpus=4",
                "--pxe",
                "--disk",
                "none",
                "--os-type=linux",
                "--os-variant=generic",
                "--noautoconsole",
                "--boot=network"
            ]
            self.virsh(virt_install, assertion=True, v=self.dev_null)
            interfaces = []
            for i in xrange(60):
                interfaces = self.fetch_discovery_interfaces()
                if len(interfaces) == 1:
                    break
                time.sleep(self.kvm_sleep_between_node)
            ip = [interfaces[0]["ipv4"]]
            self.etcd_endpoint_health(copy.deepcopy(ip))
            self.k8s_api_health(copy.deepcopy(ip))
            self.etcd_member_k8s_minions(ip[0], 1)
            self.write_ending(marker)

        finally:
            destroy, undefine = ["virsh", "destroy", "%s" % marker], \
                                ["virsh", "undefine", "%s" % marker]
            self.virsh(destroy), os.write(1, "\r")
            self.virsh(undefine), os.write(1, "\r")


if __name__ == "__main__":
    unittest.main()
