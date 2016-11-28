import json
import os
import sys
import time
import unittest
import urllib2

from app import generator

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryClient(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_api()
        cls.set_bootcfg()
        cls.set_dnsmasq()
        cls.set_rack0()
        cls.pause(5)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient00(TestKVMDiscoveryClient):
    def test_00(self):
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_00.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
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
            self.virsh(virt_install, assertion=True, v=self.dev_null)

            for i in xrange(60):
                os.write(2, "\r")
                request = urllib2.urlopen("%s/discovery/interfaces" % self.api_endpoint)
                os.write(2, "\r")
                response_body = request.read()
                request.close()
                self.assertEqual(request.code, 200)
                interfaces = json.loads(response_body)
                if interfaces["interfaces"] is not None:
                    break
                time.sleep(3)

            # Just one machine
            self.assertEqual(len(interfaces["interfaces"]), 1)

            for machine in interfaces["interfaces"]:
                # one machine with 2 interfaces [lo, eth0]
                for ifaces in machine:
                    if ifaces["name"] == "lo":
                        self.assertEqual(ifaces["netmask"], 8)
                        self.assertEqual(ifaces["IPv4"], '127.0.0.1')
                        self.assertEqual(ifaces["MAC"], '')
                        self.assertEqual(ifaces["CIDRv4"], '127.0.0.1/8')
                    else:
                        self.assertEqual(ifaces["name"], "eth0")
                        self.assertEqual(ifaces["netmask"], 21)
                        self.assertEqual(ifaces["IPv4"][:9], '172.20.0.')
                        self.assertEqual(len(ifaces["MAC"]), 17)
            self.write_ending(marker)
        finally:
            self.virsh(destroy), os.write(1, "\r")
            self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("just skip")
class TestKVMDiscoveryClient01(TestKVMDiscoveryClient):
    def test_01(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_01.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()

        interfaces = {}
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
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(3)  # KVM fail to associate nic

            for i in xrange(60):
                os.write(2, "\r")
                request = urllib2.urlopen("%s/discovery/interfaces" % self.api_endpoint)
                response_body = request.read()
                request.close()
                self.assertEqual(request.code, 200)
                interfaces = json.loads(response_body)
                if interfaces["interfaces"] is not None and \
                                len(interfaces["interfaces"]) == nb_node:
                    break
                time.sleep(3)

            # Several machines
            self.assertEqual(len(interfaces["interfaces"]), nb_node)

            for machine in interfaces["interfaces"]:
                # each machine with 2 interfaces [lo, eth0]
                for ifaces in machine:
                    if ifaces["name"] == "lo":
                        self.assertEqual(ifaces["netmask"], 8)
                        self.assertEqual(ifaces["IPv4"], '127.0.0.1')
                        self.assertEqual(ifaces["MAC"], '')
                        self.assertEqual(ifaces["CIDRv4"], '127.0.0.1/8')
                    else:
                        self.assertEqual(ifaces["name"], "eth0")
                        self.assertEqual(ifaces["netmask"], 21)
                        self.assertEqual(ifaces["IPv4"][:9], '172.20.0.')
                        self.assertEqual(len(ifaces["MAC"]), 17)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("just skip")
class TestKVMDiscoveryClient02(TestKVMDiscoveryClient):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_api()
        cls.set_bootcfg()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.set_rack0()
        cls.pause(5)

    def test_02(self):
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_02.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)

        disco_data = []
        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
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

            for i in xrange(30):
                os.write(2, "\r")
                request = urllib2.urlopen("%s/discovery" % self.api_endpoint)
                os.write(2, "\r")
                response_body = request.read()
                request.close()
                self.assertEqual(request.code, 200)
                disco_data = json.loads(response_body)
                if disco_data:
                    break
                time.sleep(6)

            self.assertEqual(len(disco_data), 1)
            for machine in disco_data:
                self.assertTrue(machine["lldp"]["is_file"])
                self.assertEqual(len(machine["lldp"]["data"]["interfaces"]), 1)

                lldp_i0 = machine["lldp"]["data"]["interfaces"][0]
                self.assertEqual(lldp_i0["chassis"]["name"][:4], "rkt-")
                self.assertEqual(len(lldp_i0["chassis"]["id"]), 17)
                self.assertEqual(len(lldp_i0["port"]["id"]), 17)

                # one machine with 2 interfaces [lo, eth0]
                for ifaces in machine["interfaces"]:
                    if ifaces["name"] == "lo":
                        self.assertEqual(ifaces["netmask"], 8)
                        self.assertEqual(ifaces["IPv4"], '127.0.0.1')
                        self.assertEqual(ifaces["MAC"], '')
                        self.assertEqual(ifaces["CIDRv4"], '127.0.0.1/8')
                    else:
                        # Have to be eth0
                        self.assertEqual(ifaces["name"], "eth0")
                        self.assertEqual(ifaces["netmask"], 21)
                        self.assertEqual(ifaces["IPv4"][:9], '172.20.0.')
                        self.assertEqual(len(ifaces["MAC"]), 17)
            self.write_ending(marker)
        finally:
            self.virsh(destroy), os.write(1, "\r")
            self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("just skip")
class TestKVMDiscoveryClient03(TestKVMDiscoveryClient):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_api()
        cls.set_bootcfg()
        cls.set_dnsmasq()
        cls.set_lldp()
        cls.set_rack0()
        cls.pause(5)

    def test_03(self):
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_03.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)

        disco_data = []
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
                time.sleep(4)  # KVM fail to associate nic

            for i in xrange(30):
                os.write(2, "\r")
                request = urllib2.urlopen("%s/discovery" % self.api_endpoint)
                os.write(2, "\r")
                response_body = request.read()
                request.close()
                self.assertEqual(request.code, 200)
                disco_data = json.loads(response_body)
                if disco_data and len(disco_data) == nb_node:
                    break
                time.sleep(6)

            # Checks
            self.assertEqual(len(disco_data), 3)

            for j, machine in enumerate(disco_data):
                self.assertTrue(machine["lldp"]["is_file"])
                self.assertEqual(len(machine["lldp"]["data"]["interfaces"]), 1)

                lldp_i = machine["lldp"]["data"]["interfaces"][0]
                self.assertEqual(lldp_i["chassis"]["name"][:4], "rkt-")
                self.assertEqual(len(lldp_i["chassis"]["id"]), 17)
                self.assertEqual(len(lldp_i["port"]["id"]), 17)

                # Each machine with 2 interfaces [lo, eth0]
                for i in machine["interfaces"]:
                    if i["name"] == "lo":
                        self.assertEqual(i["netmask"], 8)
                        self.assertEqual(i["IPv4"], '127.0.0.1')
                        self.assertEqual(i["MAC"], '')
                        self.assertEqual(i["CIDRv4"], '127.0.0.1/8')
                    else:
                        # Have to be eth0
                        self.assertEqual(i["name"], "eth0")
                        self.assertEqual(i["netmask"], 21)
                        self.assertEqual(i["IPv4"][:9], '172.20.0.')
                        self.assertEqual(len(i["MAC"]), 17)
            self.write_ending(marker)
        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")
                time.sleep(1)


# @unittest.skip("just skip")
class TestKVMDiscoveryClient04(TestKVMDiscoveryClient):
    def test_04(self):
        marker = "euid-%s-%s" % (TestKVMDiscoveryClient.__name__.lower(), self.test_04.__name__)
        os.environ["BOOTCFG_IP"] = "172.20.0.1"
        os.environ["API_IP"] = "172.20.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
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

            disco_data = []
            for i in xrange(30):
                os.write(2, "\r")
                request = urllib2.urlopen("%s/discovery" % self.api_endpoint)
                os.write(2, "\r")
                response_body = request.read()
                request.close()
                self.assertEqual(request.code, 200)
                disco_data = json.loads(response_body)
                if disco_data and len(disco_data) == 1:
                    break
                time.sleep(6)

            self.assertEqual(1, len(disco_data))
            self.assertIs(type(disco_data[0]["ignition-journal"]), list)
            self.assertTrue(len(disco_data[0]["ignition-journal"]) > 0)
            self.write_ending(marker)

        finally:
            self.virsh(destroy), os.write(1, "\r")
            self.virsh(undefine), os.write(1, "\r")


if __name__ == "__main__":
    unittest.main()
