import unittest
import os
import sys

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import kvm_player


class TestKernelVirtualMachinePlayer(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_rack0()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.pause(cls.wait_setup_teardown)

    def test(self):
        marker = "%s" % TestKernelVirtualMachinePlayer.__name__.lower()
        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
                "--network=bridge:rack0,model=virtio",
                "--memory=1024",
                "--vcpus=1",
                "--pxe",
                "--disk",
                "none",
                "--os-type=linux",
                "--os-variant=generic",
                "--noautoconsole",
                "--boot=network"
            ]
            self.virsh(virt_install, assertion=True)
            self.pause(5)
        finally:
            self.virsh(destroy), os.write(1, "\r")
            self.virsh(undefine), os.write(1, "\r")


# This have to raise
# class TestKernelVirtualMachinePlayerRaise(kvm_player.KernelVirtualMachinePlayer):
#     def test(self):
#         pass


if __name__ == '__main__':
    unittest.main()
