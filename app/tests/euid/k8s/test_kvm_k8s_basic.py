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


class TestKVMK8sBasic(kvm_player.KernelVirtualMachinePlayer):
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
class TestKVMK8SBasic0(TestKVMK8sBasic):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 2
        marker = "euid-%s-%s" % (TestKVMK8sBasic.__name__.lower(), self.test_00.__name__)
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
            for i, m in enumerate(nodes):
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=%d" % (self.host_total_memory_mib() // 2),
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
                time.sleep(self.kvm_sleep_between_node)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            sch_member.etcd_members_nb = 1

            time.sleep(self.kvm_sleep_between_node * nb_node)
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertTrue(sch_member.apply())

            sch_cp = scheduler.K8sControlPlaneScheduler(
                etcd_member_instance=sch_member,
                ignition_control_plane="%s-k8s-control-plane" % marker,
                apply_first=False
            )
            sch_cp.control_plane_nb = 1
            for i in xrange(60):
                if sch_cp.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertTrue(sch_cp.apply())
            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.kvm_sleep_between_node * nb_node)
            self.etcd_member_len(sch_member.ip_list[0], sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_cp.ip_list)
            self.k8s_api_health(sch_cp.ip_list)
            self.etcd_member_k8s_minions(sch_member.ip_list[0], sch_cp.control_plane_nb)
            self.write_ending(marker)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


# @unittest.skip("")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMK8SBasic1(TestKVMK8sBasic):
    # @unittest.skip("just skip")
    def test_01(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMK8sBasic.__name__.lower(), self.test_01.__name__)
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
            for i, m in enumerate(nodes):
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=%d" % (self.host_total_memory_mib() // 2),
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

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            sch_member.etcd_members_nb = 1
            time.sleep(self.kvm_sleep_between_node * nb_node)
            for i in xrange(60):
                if sch_member.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertTrue(sch_member.apply())

            sch_cp = scheduler.K8sControlPlaneScheduler(
                etcd_member_instance=sch_member,
                ignition_control_plane="%s-k8s-control-plane" % marker,
                apply_first=False
            )
            sch_cp.control_plane_nb = 1
            for i in xrange(60):
                if sch_cp.apply() is True:
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertTrue(sch_cp.apply())
            sch_no = scheduler.K8sNodeScheduler(
                k8s_control_plane=sch_cp,
                ignition_node="%s-k8s-node" % marker,
                apply_first=False
            )
            for i in xrange(60):
                if sch_no.apply() == 1:
                    break
                time.sleep(self.kvm_sleep_between_node)

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.kvm_sleep_between_node * nb_node)

            self.etcd_member_len(sch_member.ip_list[0], sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_cp.ip_list)
            self.k8s_api_health(sch_cp.ip_list)
            self.etcd_member_k8s_minions(sch_member.ip_list[0], len(sch_no.wide_done_list) - sch_member.etcd_members_nb)
            self.write_ending(marker)
        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


if __name__ == "__main__":
    unittest.main()
