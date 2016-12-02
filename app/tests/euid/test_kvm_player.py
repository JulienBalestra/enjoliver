import unittest

import kvm_player


class TestKernelVirtualMachinePlayer(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_rack0()
        cls.set_api()
        cls.set_bootcfg()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.pause(cls.wait_setup_teardown)

    def test(self):
        pass


# This have to raise
# class TestKernelVirtualMachinePlayerRaise(kvm_player.KernelVirtualMachinePlayer):
#     def test(self):
#         pass


if __name__ == '__main__':
    unittest.main()
