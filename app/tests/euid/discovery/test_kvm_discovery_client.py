import os
import sys
import time
import unittest

from app import generator

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


class TestKVMDiscoveryClient(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.set_rack0()
        cls.running_requirements()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient00(TestKVMDiscoveryClient):
    """
    node_nb: 1

    Interfaces
    """

    def test_00(self):
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_00.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path
        )
        gen.dumps()

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        interfaces = {}
        try:
            virt_install = self.create_virtual_machine(marker, 1)
            self.virsh(virt_install, assertion=True, v=self.dev_null)

            for i in range(60):
                interfaces = self.fetch_discovery_interfaces()
                if len(interfaces) > 0:
                    break
                time.sleep(self.testing_sleep_seconds)

            # Just one machine
            self.assertEqual(len(interfaces), 1)
            for i in interfaces:
                self.assertEqual(i["name"], "eth0")
                self.assertEqual(i["netmask"], 16)
                self.assertEqual(i["ipv4"][:9], '172.20.0.')
                self.assertEqual(len(i["mac"]), 17)
                self.assertTrue(i["as_boot"])

            self.write_ending(marker)
        finally:
            self.virsh(destroy)
            self.virsh(undefine)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient01(TestKVMDiscoveryClient):
    """
    node_nb: 3

    Interfaces
    """

    def test_01(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_01.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path
        )
        gen.dumps()

        interfaces = {}
        try:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % machine_marker,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=1024",
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
                time.sleep(self.testing_sleep_seconds)  # KVM fail to associate nic

            for i in range(60):
                interfaces = self.fetch_discovery_interfaces()
                if len(interfaces) == nb_node:
                    break
                time.sleep(self.testing_sleep_seconds)

            # Several machines
            self.assertEqual(len(interfaces), nb_node)

            for i in interfaces:
                self.assertEqual(i["name"], "eth0")
                self.assertEqual(i["netmask"], 16)
                self.assertEqual(i["ipv4"][:9], '172.20.0.')
                self.assertEqual(len(i["mac"]), 17)
                self.assertTrue(i["as_boot"])

            self.write_ending(marker)

        finally:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy)
                self.virsh(undefine)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient02(TestKVMDiscoveryClient):
    """
    node_nb: 1

    Interfaces
    LLDP
    """

    @classmethod
    def setUpClass(cls):
        cls.running_requirements()
        cls.set_acserver()
        cls.set_rack0()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.pause(cls.wait_setup_teardown)

    def test_02(self):
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_02.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path,
            extra_metadata={
                "lldp_image_url": self.ec.lldp_image_url,
                "etc_hosts": self.ec.etc_hosts,

            }
        )
        gen.dumps()

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)

        interfaces = []
        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
                "--network=bridge:rack0,model=virtio",
                "--memory=2048",
                "--vcpus=%d" % self.get_optimized_cpu(1),
                "--pxe",
                "--disk",
                "none",
                "--os-type=linux",
                "--os-variant=generic",
                "--noautoconsole",
                "--boot=network"
            ]
            self.virsh(virt_install, assertion=True, v=self.dev_null)

            for i in range(60):
                interfaces = self.fetch_discovery_interfaces()
                if len(interfaces) > 0:
                    break
                time.sleep(self.testing_sleep_seconds)

            self.assertEqual(len(interfaces), 1)
            for interface in interfaces:
                self.assertIsNotNone(interface["chassis_name"])
                self.assertEqual(interface["name"], "eth0")
                self.assertEqual(interface["netmask"], 16)
                self.assertEqual(interface["ipv4"][:9], '172.20.0.')
                self.assertEqual(len(interface["mac"]), 17)
                self.assertTrue(interface["as_boot"])

            self.write_ending(marker)
        finally:
            self.virsh(destroy)
            self.virsh(undefine)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient03(TestKVMDiscoveryClient):
    """
    node_nb: 3

    Interfaces
    LLDP
    """

    @classmethod
    def setUpClass(cls):
        cls.running_requirements()
        cls.set_acserver()
        cls.set_rack0()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.pause(cls.wait_setup_teardown)

    def test_03(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_03.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path,
            extra_metadata={
                "lldp_image_url": self.ec.lldp_image_url,
                "etc_hosts": self.ec.etc_hosts,
            }
        )
        gen.dumps()

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)

        interfaces = []
        try:
            for i in range(nb_node):
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
                    "--vcpus=%d" % self.get_optimized_cpu(1),
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)  # KVM fail to associate nic

            for i in range(60):
                interfaces = self.fetch_discovery_interfaces()
                if len(interfaces) == nb_node:
                    break
                time.sleep(self.testing_sleep_seconds)

            # Checks
            self.assertEqual(len(interfaces), 3)

            for interface in interfaces:
                self.assertIsNotNone(interface["chassis_name"])
                self.assertEqual(interface["name"], "eth0")
                self.assertEqual(interface["netmask"], 16)
                self.assertEqual(interface["ipv4"][:9], '172.20.0.')
                self.assertEqual(len(interface["mac"]), 17)
                self.assertTrue(interface["as_boot"])

            self.assertEqual(1, len(set([k["chassis_name"] for k in interfaces])))

            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage()
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy)
                self.virsh(undefine)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient04(TestKVMDiscoveryClient):
    """
    Ignition Journal
    """

    def test_04(self):
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_04.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path,
            extra_metadata={
                "lldp_image_url": self.ec.lldp_image_url,
                "etc_hosts": self.ec.etc_hosts,
            }
        )
        gen.dumps()

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
                "--network=bridge:rack0,model=virtio",
                "--memory=1024",
                "--vcpus=%d" % self.get_optimized_cpu(1),
                "--pxe",
                "--disk",
                "none",
                "--os-type=linux",
                "--os-variant=generic",
                "--noautoconsole",
                "--boot=network"
            ]
            self.virsh(virt_install, assertion=True, v=self.dev_null)

            disco_data = dict()
            for i in range(60):
                disco_data = self.fetch_discovery()
                if disco_data and len(disco_data) == 1:
                    break
                time.sleep(self.testing_sleep_seconds)

            self.assertEqual(1, len(disco_data))
            lines = self.fetch_discovery_ignition_journal(disco_data[0]["boot-info"]["uuid"])
            self.assertIs(type(lines), list)
            self.assertTrue(len(lines) > 0)
            self.write_ending(marker)

        finally:
            self.virsh(destroy)
            self.virsh(undefine)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient05(TestKVMDiscoveryClient):
    """
    node_nb: 1 2 interfaces

    Interfaces
    """

    def test_05(self):
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_05.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path,
            extra_metadata={
                "lldp_image_url": self.ec.lldp_image_url,
                "etc_hosts": self.ec.etc_hosts,
            }
        )
        gen.dumps()

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        interfaces = {}
        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
                "--network=bridge:rack0,model=virtio",
                "--network=bridge:rack0,model=virtio",
                "--memory=1024",
                "--vcpus=%d" % self.get_optimized_cpu(1),
                "--pxe",
                "--disk",
                "none",
                "--os-type=linux",
                "--os-variant=generic",
                "--noautoconsole",
                "--boot=network"
            ]
            self.virsh(virt_install, assertion=True, v=self.dev_null)

            for i in range(60):
                interfaces = self.fetch_discovery_interfaces()
                if len(interfaces) > 0:
                    break
                time.sleep(self.testing_sleep_seconds)

            # Just one machine but with 2 interfaces
            self.assertEqual(len(interfaces), 2)
            for i in interfaces:
                self.assertEqual(i["netmask"], 16)
                self.assertEqual(i["ipv4"][:9], '172.20.0.')
                self.assertEqual(len(i["mac"]), 17)

                try:
                    self.assertTrue(i["as_boot"])
                except AssertionError:
                    self.assertFalse(i["as_boot"])
                try:
                    self.assertEqual(i["name"], "eth0")
                except AssertionError:
                    self.assertEqual(i["name"], "eth1")

            self.write_ending(marker)
        finally:
            self.virsh(destroy)
            self.virsh(undefine)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient06(TestKVMDiscoveryClient):
    """
    node_nb: 3 with 4 interfaces

    Interfaces
    """

    def test_06(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_06.__name__)
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path,
            extra_metadata={
                "lldp_image_url": self.ec.lldp_image_url,
                "etc_hosts": self.ec.etc_hosts,
            }
        )
        gen.dumps()

        interfaces = {}
        try:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % machine_marker,
                    "--network=bridge:rack0,model=virtio",
                    "--network=bridge:rack0,model=virtio",
                    "--network=bridge:rack0,model=virtio",
                    "--network=bridge:rack0,model=virtio",
                    "--memory=1024",
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
                time.sleep(self.testing_sleep_seconds)  # KVM fail to associate nic

            for i in range(60):
                interfaces = self.fetch_discovery_interfaces()
                if len(interfaces) == nb_node * 4:
                    break
                time.sleep(self.testing_sleep_seconds)

            # Just one machine but with 4 interfaces
            self.assertEqual(len(interfaces), 4 * nb_node)
            as_boot = 0
            as_not_boot = 0
            for i in interfaces:
                self.assertEqual(i["netmask"], 16)
                self.assertEqual(i["ipv4"][:9], '172.20.0.')
                self.assertEqual(len(i["mac"]), 17)

                try:
                    self.assertTrue(i["as_boot"])
                    as_boot += 1
                except AssertionError:
                    self.assertFalse(i["as_boot"])
                    as_not_boot += 1
            self.assertEqual(as_boot, nb_node)
            self.assertEqual(as_not_boot, nb_node * 3)
            self.write_ending(marker)

        finally:
            for i in range(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy)
                self.virsh(undefine)


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
