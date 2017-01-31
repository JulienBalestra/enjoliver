import copy
import os
import sys
import time
import unittest

from app import generator, scheduler

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


@unittest.skipIf(os.geteuid() != 0, "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_rack0()
        cls.set_api()
        cls.set_bootcfg()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler0(TestKVMDiscoveryScheduler):
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryScheduler.__name__.lower(), self.test_00.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()

        try:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % machine_marker,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=2048",
                    "--vcpus=1",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic

            time.sleep(nb_node * self.kvm_sleep_between_node)
            sch = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            sch.etcd_members_nb = 1
            for i in xrange(60):
                if sch.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)
            self.assertTrue(sch.apply())

            os.write(2, "\r-> start reboot nodes\n\r")
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                reset = ["virsh", "reset", "%s" % machine_marker]
                self.virsh(reset), os.write(1, "\r")
                time.sleep(self.kvm_sleep_between_node)
                start = ["virsh", "start", "%s" % machine_marker]
                self.virsh(start), os.write(1, "\r")
                time.sleep(self.kvm_sleep_between_node)
            os.write(2, "\r-> start reboot asked\n\r")

            time.sleep(nb_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(sch.ip_list)
            self.etcd_member_len(sch.ip_list[0], sch.etcd_members_nb)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler1(TestKVMDiscoveryScheduler):
    def test_01(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryScheduler.__name__.lower(), self.test_01.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()

        try:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % machine_marker,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=2048",
                    "--vcpus=1",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic

            time.sleep(nb_node * self.kvm_sleep_between_node)
            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)
            self.assertTrue(sch_member.apply())

            os.write(2, "\r-> start reboot nodes\n\r")
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                reset = ["virsh", "reset", "%s" % machine_marker]
                self.virsh(reset), os.write(1, "\r")
                time.sleep(self.kvm_sleep_between_node)
                start = ["virsh", "start", "%s" % machine_marker]
                self.virsh(start), os.write(1, "\r")
                time.sleep(self.kvm_sleep_between_node)
            os.write(2, "\r-> start reboot asked\n\r")

            time.sleep(nb_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(sch_member.ip_list)
            # regarding the ignition deployment, all etcd are solo even in clustering scheduler
            for etcd_solo in sch_member.ip_list:
                self.etcd_member_len(etcd_solo, 1)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler2(TestKVMDiscoveryScheduler):
    def test_02(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryScheduler.__name__.lower(), self.test_02.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()

        try:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % machine_marker,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=2048",
                    "--vcpus=1",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic
            time.sleep(nb_node * self.kvm_sleep_between_node)
            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)
            self.assertTrue(sch_member.apply())

            os.write(2, "\r-> start reboot nodes\n\r")
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                reset = ["virsh", "reset", "%s" % machine_marker]
                self.virsh(reset), os.write(1, "\r")
                time.sleep(self.kvm_sleep_between_node)
                start = ["virsh", "start", "%s" % machine_marker]
                self.virsh(start), os.write(1, "\r")
                time.sleep(self.kvm_sleep_between_node)
            os.write(2, "\r-> start reboot asked\n\r")

            time.sleep(nb_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(sch_member.ip_list)
            self.etcd_member_len(sch_member.ip_list[0], sch_member.etcd_members_nb)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler3(TestKVMDiscoveryScheduler):
    def test_03(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryScheduler.__name__.lower(), self.test_03.__name__)
        nodes = ["%s-%d" % (marker, i) for i in xrange(nb_node)]
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()
        for m in nodes:
            destroy, undefine = ["virsh", "destroy", m], \
                                ["virsh", "undefine", m]
            self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            for m in nodes:
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=2048",
                    "--vcpus=1",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            time.sleep(nb_node * self.kvm_sleep_between_node)
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)
            self.assertTrue(sch_member.apply())

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            time.sleep(nb_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(sch_member.ip_list)
            self.etcd_member_len(sch_member.ip_list[0], sch_member.etcd_members_nb)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


"""
=> Below KVM Instance will auto shutdown and testing suite will reboot them
"""


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler4(TestKVMDiscoveryScheduler):
    def test_04(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 4
        marker = "euid-%s-%s" % (TestKVMDiscoveryScheduler.__name__.lower(), self.test_04.__name__)
        nodes = ["%s-%d" % (marker, i) for i in xrange(nb_node)]
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()
        for m in nodes:
            destroy, undefine = ["virsh", "destroy", m], \
                                ["virsh", "undefine", m]
            self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            for m in nodes:
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=2048",
                    "--vcpus=1",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            time.sleep(nb_node * self.kvm_sleep_between_node)
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertTrue(sch_member.apply())
            sch_proxy = scheduler.EtcdProxyScheduler(
                dep_instance=sch_member,
                ignition_proxy="%s-emember" % marker,
                apply_first=False
            )
            time.sleep(nb_node * self.kvm_sleep_between_node)
            for i in xrange(60):
                if sch_proxy.apply() == 1:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertEqual(sch_proxy.apply(), 1)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            time.sleep(nb_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(sch_member.ip_list)
            self.etcd_member_len(sch_member.ip_list[0], sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_proxy.ip_list)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler5(TestKVMDiscoveryScheduler):
    def test_05(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 5
        marker = "euid-%s-%s" % (TestKVMDiscoveryScheduler.__name__.lower(), self.test_05.__name__)
        nodes = ["%s-%d" % (marker, i) for i in xrange(nb_node)]
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()
        for m in nodes:
            destroy, undefine = ["virsh", "destroy", m], \
                                ["virsh", "undefine", m]
            self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            for m in nodes:
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=2048",
                    "--vcpus=1",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )

            time.sleep(nb_node * self.kvm_sleep_between_node)
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)
            self.assertTrue(sch_member.apply())

            sch_proxy = scheduler.EtcdProxyScheduler(
                dep_instance=sch_member,
                ignition_proxy="%s-emember" % marker,
                apply_first=False
            )
            for i in xrange(60):
                if sch_proxy.apply() == 2:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertEqual(sch_proxy.apply(), 2)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            time.sleep(nb_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(sch_member.ip_list)
            self.etcd_member_len(sch_member.ip_list[0], sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_proxy.ip_list)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler6(TestKVMDiscoveryScheduler):
    def test_06(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 5
        marker = "euid-%s-%s" % (TestKVMDiscoveryScheduler.__name__.lower(), self.test_06.__name__)
        nodes = ["%s-%d" % (marker, i) for i in xrange(nb_node)]
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()
        for m in nodes:
            destroy, undefine = ["virsh", "destroy", m], \
                                ["virsh", "undefine", m]
            self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            for m in nodes:
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=2048",
                    "--vcpus=1",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_uri,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            sch_member.etcd_members_nb = 1

            time.sleep(nb_node * self.kvm_sleep_between_node)
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertTrue(sch_member.apply())
            sch_proxy = scheduler.EtcdProxyScheduler(
                dep_instance=sch_member,
                ignition_proxy="%s-emember" % marker,
                apply_first=False
            )
            for i in xrange(60):
                if sch_proxy.apply() == 4:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertEqual(sch_proxy.apply(), 4)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            time.sleep(nb_node * self.kvm_sleep_between_node)

            self.etcd_endpoint_health(sch_member.ip_list)
            self.etcd_member_len(sch_member.ip_list[0], sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_proxy.ip_list)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


if __name__ == "__main__":
    unittest.main(failfast=True, defaultTest=os.getenv("TEST"))
