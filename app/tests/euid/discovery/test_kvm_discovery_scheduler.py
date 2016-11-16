import copy
import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib2
from multiprocessing import Process
from unittest import TestCase

from app import api
from app import generator
from app import scheduler


def pause(s=200):
    try:
        os.write(2, "\r==> sleep %d...\n\r" % s)
        time.sleep(s)
    except KeyboardInterrupt:
        pass
    finally:
        os.write(2, "\r==> sleep finish\n\r" % s)


@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler(TestCase):
    p_bootcfg = Process
    p_dnsmasq = Process
    p_api = Process
    p_lldp = Process
    gen = generator.Generator

    basic_path = "%s" % os.path.dirname(os.path.abspath(__file__))
    euid_path = "%s" % os.path.dirname(basic_path)
    tests_path = "%s" % os.path.split(euid_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path
    assets_path = "%s/bootcfg/assets" % project_path

    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    bootcfg_port = int(os.getenv("BOOTCFG_PORT", "8080"))

    bootcfg_address = "0.0.0.0:%d" % bootcfg_port
    bootcfg_endpoint = "http://localhost:%d" % bootcfg_port

    api_port = int(os.getenv("API_PORT", "5000"))

    api_host = "172.20.0.1"
    api_endpoint = "http://%s:%d" % (api_host, api_port)

    dev_null = None

    @staticmethod
    def process_target_bootcfg():
        cmd = [
            "%s/bootcfg_dir/bootcfg" % TestKVMDiscoveryScheduler.tests_path,
            "-data-path", "%s" % TestKVMDiscoveryScheduler.test_bootcfg_path,
            "-assets-path", "%s" % TestKVMDiscoveryScheduler.assets_path,
            "-address", "%s" % TestKVMDiscoveryScheduler.bootcfg_address,
            "-log-level", "debug"
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def process_target_api():
        api.cache.clear()
        api.app.run(host=TestKVMDiscoveryScheduler.api_host, port=TestKVMDiscoveryScheduler.api_port)

    @staticmethod
    def process_target_dnsmasq():
        cmd = [
            "%s/rkt_dir/rkt" % TestKVMDiscoveryScheduler.tests_path,
            "--local-config=%s" % TestKVMDiscoveryScheduler.tests_path,
            "--mount",
            "volume=config,target=/etc/dnsmasq.conf",
            "--mount",
            "volume=resolv,target=/etc/resolv.conf",
            "run",
            "quay.io/coreos/dnsmasq:v0.3.0",
            "--insecure-options=all",
            "--net=host",
            "--interactive",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--uuid-file-save=/tmp/dnsmasq.uuid",
            "--volume",
            "resolv,kind=host,source=/etc/resolv.conf",
            "--volume",
            "config,kind=host,source=%s/dnsmasq-rack0.conf" % TestKVMDiscoveryScheduler.tests_path
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)
        os._exit(2)

    @staticmethod
    def fetch_lldpd():
        cmd = [
            "%s/rkt_dir/rkt" % TestKVMDiscoveryScheduler.tests_path,
            "--local-config=%s" % TestKVMDiscoveryScheduler.tests_path,
            "fetch",
            "--insecure-options=all",
            "%s/lldp/serve/static-aci-lldp-0.aci" % TestKVMDiscoveryScheduler.assets_path]
        assert subprocess.call(cmd) == 0

    @staticmethod
    def process_target_lldpd():
        cmd = [
            "%s/rkt_dir/rkt" % TestKVMDiscoveryScheduler.tests_path,
            "--local-config=%s" % TestKVMDiscoveryScheduler.tests_path,
            "run",
            "static-aci-lldp",
            "--insecure-options=all",
            "--net=host",
            "--interactive",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--exec",
            "/usr/sbin/lldpd",
            "--",
            "-dd"]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)
        os._exit(2)  # Should not happen

    @staticmethod
    def process_target_create_rack0():
        cmd = [
            "%s/rkt_dir/rkt" % TestKVMDiscoveryScheduler.tests_path,
            "--local-config=%s" % TestKVMDiscoveryScheduler.tests_path,
            "run",
            "quay.io/coreos/dnsmasq:v0.3.0",
            "--insecure-options=all",
            "--net=rack0",
            "--interactive",
            "--set-env=TERM=%s" % os.getenv("TERM", "xterm"),
            "--exec",
            "/bin/true"]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)
        os._exit(2)  # Should not happen

    @staticmethod
    def dns_masq_running():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = 1
        for i in xrange(120):
            result = sock.connect_ex(('172.20.0.1', 53))
            if result == 0:
                break
            time.sleep(0.5)
            if i % 10 == 0:
                os.write(1, "DNSMASQ still NOT ready\n\r")
        assert result == 0
        os.write(1, "DNSMASQ ready\n\r")
        sys.stdout.flush()

    @classmethod
    def generator(cls):
        marker = "%s" % cls.__name__.lower()
        ignition_file = "sudo-%s.yaml" % marker

        cls.gen = generator.Generator(
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            bootcfg_path=cls.test_bootcfg_path)

        cls.gen.dumps()

    @classmethod
    def setUpClass(cls):
        if os.geteuid() != 0:
            raise RuntimeError("Need to be root EUID==%d" % os.geteuid())

        cls.clean_sandbox()

        if os.path.isfile("%s/rkt_dir/rkt" % TestKVMDiscoveryScheduler.tests_path) is False or \
                        os.path.isfile("%s/bootcfg_dir/bootcfg" % TestKVMDiscoveryScheduler.tests_path) is False:
            os.write(2, "Call 'make' as user for:\n"
                        "- %s/rkt_dir/rkt\n" % TestKVMDiscoveryScheduler.tests_path +
                     "- %s/bootcfg_dir/bootcfg\n" % TestKVMDiscoveryScheduler.tests_path)
            exit(2)

        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_bootcfg = Process(target=TestKVMDiscoveryScheduler.process_target_bootcfg)
        cls.p_bootcfg.start()
        assert cls.p_bootcfg.is_alive() is True

        p_create_rack0 = Process(
            target=TestKVMDiscoveryScheduler.process_target_create_rack0)
        p_create_rack0.start()
        p_create_rack0.join(5)
        os.write(1, "\rBridge w/ iptables creation exitcode:%d\n\r" % p_create_rack0.exitcode)
        assert subprocess.call(["ip", "link", "show", "rack0"]) == 0

        cls.p_dnsmasq = Process(target=TestKVMDiscoveryScheduler.process_target_dnsmasq)
        cls.p_dnsmasq.start()
        assert cls.p_dnsmasq.is_alive() is True
        TestKVMDiscoveryScheduler.dns_masq_running()

        cls.p_api = Process(target=TestKVMDiscoveryScheduler.process_target_api)
        cls.p_api.start()
        assert cls.p_api.is_alive() is True

        cls.fetch_lldpd()
        cls.p_lldp = Process(target=TestKVMDiscoveryScheduler.process_target_lldpd)
        cls.p_lldp.start()
        assert cls.p_lldp.is_alive() is True

        cls.dev_null = open("/dev/null", "w")

    @classmethod
    def tearDownClass(cls):
        os.write(1, "\n\rTERM -> %d\n\r" % cls.p_bootcfg.pid)
        sys.stdout.flush()
        cls.p_bootcfg.terminate()
        cls.p_bootcfg.join(timeout=5)
        cls.p_dnsmasq.terminate()
        cls.p_dnsmasq.join(timeout=5)
        cls.p_api.terminate()
        cls.p_api.join(timeout=5)
        cls.p_lldp.terminate()
        cls.p_lldp.join(timeout=5)
        # cls.clean_sandbox()
        subprocess.call([
            "%s/rkt_dir/rkt" % TestKVMDiscoveryScheduler.tests_path,
            "--local-config=%s" % TestKVMDiscoveryScheduler.tests_path,
            "gc",
            "--grace-period=0s"])
        cls.dev_null.close()

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestKVMDiscoveryScheduler.test_bootcfg_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s\n\r" % f)
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_bootcfg.is_alive())
        self.assertTrue(self.p_dnsmasq.is_alive())
        self.assertTrue(self.p_api.is_alive())
        self.assertTrue(self.p_lldp.is_alive())

        self.clean_sandbox()
        for i in xrange(10):
            try:
                self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
            except urllib2.URLError:
                time.sleep(0.5)

    def virsh(self, cmd, assertion=False, v=None):
        if v is not None:
            os.write(1, "\r-> " + " ".join(cmd) + "\n\r")
            sys.stdout.flush()
        ret = subprocess.call(cmd, stdout=v, stderr=v)
        if assertion is True and ret != 0:
            raise RuntimeError("\"%s\"" % " ".join(cmd))

    def fetch_discovery_interfaces(self):
        request = urllib2.urlopen("%s/discovery/interfaces" % self.api_endpoint)
        response_body = request.read()
        request.close()
        self.assertEqual(request.code, 200)
        interfaces = json.loads(response_body)
        return interfaces

    def fetch_discovery(self):
        request = urllib2.urlopen("%s/discovery" % self.api_endpoint)
        response_body = request.read()
        request.close()
        self.assertEqual(request.code, 200)
        disco_data = json.loads(response_body)
        return disco_data

    def kvm_restart_off_machines(self, to_start, tries=60):
        for j in xrange(tries):
            if len(to_start) == 0:
                break

            for i, m in enumerate(to_start):
                start = ["virsh", "start", "%s" % m]
                try:
                    self.virsh(start, assertion=True), os.write(1, "\r")
                    to_start.pop(i)
                    time.sleep(4)

                except RuntimeError:
                    # virsh raise this
                    pass

            time.sleep(2)
        self.assertEqual(len(to_start), 0)

    def etcd_endpoint_health(self, ips, tries=15):
        for t in xrange(tries):
            for i, ip in enumerate(ips):
                try:
                    endpoint = "http://%s:2379/health" % ip
                    request = urllib2.urlopen(endpoint)
                    response_body = json.loads(request.read())
                    request.close()
                    os.write(1, "\r-> RESULT %s %s\n\r" % (endpoint, response_body))
                    sys.stdout.flush()
                    if response_body == {u"health": u"true"}:
                        ips.pop(i)
                        os.write(1, "\r-> REMAIN %s\n\r" % str(ips))

                except urllib2.URLError:
                    os.write(2, "\r-> NOT READY %s\n\r" % ip)
                    time.sleep(6)
        self.assertEqual(len(ips), 0)


# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler0(TestKVMDiscoveryScheduler):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
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
                time.sleep(4)  # KVM fail to associate nic

            time.sleep(10)
            sch = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            sch.etcd_members_nb = 1

            for i in xrange(30):
                if sch.apply() is True:
                    break
                time.sleep(6)

            self.assertTrue(sch.apply())

            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                reset = ["virsh", "reset", "%s" % machine_marker]
                self.virsh(reset), os.write(1, "\r")

            time.sleep(1)

            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                start = ["virsh", "start", "%s" % machine_marker]
                self.virsh(start), os.write(1, "\r")
                time.sleep(3)

            ips = sch.ip_list

            one_etcd = False
            for i in xrange(30):
                for ip in ips:
                    try:
                        endpoint = "http://%s:2379/health" % ip
                        request = urllib2.urlopen(endpoint)
                        response_body = json.loads(request.read())
                        request.close()
                        if response_body == {u'health': u'true'}:
                            # one_etcd = Just One
                            self.assertFalse(one_etcd)
                            one_etcd = True
                            os.write(2, "\r%s %s\n\r" % (endpoint, response_body))
                            break

                    except urllib2.URLError:
                        pass

                if one_etcd is True:
                    break

                time.sleep(2)

            self.assertTrue(one_etcd)

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
        self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
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
                time.sleep(4)  # KVM fail to associate nic

            time.sleep(10)
            sch = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )

            for i in xrange(30):
                if sch.apply() is True:
                    break
                time.sleep(6)

            self.assertTrue(sch.apply())

            os.write(2, "\r-> start reboot nodes\n\r")

            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                reset = ["virsh", "reset", "%s" % machine_marker]
                self.virsh(reset), os.write(1, "\r")

            time.sleep(1)

            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                start = ["virsh", "start", "%s" % machine_marker]
                self.virsh(start), os.write(1, "\r")
                time.sleep(3)

            os.write(2, "\r-> start reboot asked\n\r")

            ips = sch.ip_list

            etcd = 0
            for i in xrange(30):
                for ip in ips:
                    try:
                        endpoint = "http://%s:2379/health" % ip
                        request = urllib2.urlopen(endpoint)
                        response_body = json.loads(request.read())
                        request.close()
                        if response_body == {u'health': u'true'}:
                            etcd += 1
                            os.write(2, "\r%s %s\n\r" % (endpoint, response_body))
                            if etcd == nb_node:
                                break

                    except urllib2.URLError:
                        pass

                if etcd == nb_node:
                    break

                time.sleep(2)
            self.assertTrue(etcd == nb_node)

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
    # @unittest.skip("just skip")
    def test_02(self):
        self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
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
                time.sleep(3)  # KVM fail to associate nic

            sch = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )

            time.sleep(10)
            for i in xrange(30):
                if sch.apply() is True:
                    break
                time.sleep(6)

            self.assertTrue(sch.apply())

            os.write(2, "\r-> start reboot nodes\n\r")

            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                reset = ["virsh", "reset", "%s" % machine_marker]
                self.virsh(reset), os.write(1, "\r")
                time.sleep(2)
                start = ["virsh", "start", "%s" % machine_marker]
                self.virsh(start), os.write(1, "\r")
                time.sleep(2)

            os.write(2, "\r-> start reboot asked\n\r")

            ips_collected = sch.ip_list

            for i in xrange(30):
                try:
                    endpoint = "http://%s:2379/v2/members" % ips_collected[0]
                    request = urllib2.urlopen(endpoint)
                    response_body = json.loads(request.read())
                    request.close()
                    if len(response_body["members"]) == nb_node:
                        break
                except urllib2.URLError:
                    pass

                time.sleep(6)

            endpoint = "http://%s:2379/v2/members" % ips_collected[0]
            request = urllib2.urlopen(endpoint)
            response_body = json.loads(request.read())
            request.close()
            self.assertEqual(len(response_body["members"]), nb_node)

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
    # @unittest.skip("just skip")
    def test_03(self):
        self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
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
                time.sleep(3)  # KVM fail to associate nic

            sch = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )

            time.sleep(10)
            for i in xrange(30):
                if sch.apply() is True:
                    break
                time.sleep(6)

            self.assertTrue(sch.apply())

            # TODO -> KVM doesn't restart itself
            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            ips_collected = sch.ip_list

            for i in xrange(20):
                try:
                    endpoint = "http://%s:2379/v2/members" % ips_collected[0]
                    request = urllib2.urlopen(endpoint)
                    response_body = json.loads(request.read())
                    request.close()
                    if len(response_body["members"]) == nb_node:
                        break
                except urllib2.URLError:
                    pass

                time.sleep(6)

            endpoint = "http://%s:2379/v2/members" % ips_collected[0]
            request = urllib2.urlopen(endpoint)
            response_body = json.loads(request.read())
            request.close()
            self.assertEqual(len(response_body["members"]), nb_node)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


#
# => Below KVM Instance will auto shutdown and testing suite will reboot them
#

# @unittest.skip("skip")
@unittest.skipIf(os.geteuid() != 0,
                 "TestKVMDiscovery need privilege")
class TestKVMDiscoveryScheduler4(TestKVMDiscoveryScheduler):
    # @unittest.skip("just skip")
    def test_04(self):
        self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
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
                time.sleep(3)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )

            time.sleep(10)
            for i in xrange(30):
                if sch_member.apply() is True:
                    break
                time.sleep(6)

            self.assertTrue(sch_member.apply())
            sch_proxy = scheduler.EtcdProxyScheduler(
                etcd_member_instance=sch_member,
                ignition_proxy="%s-emember" % marker,
                apply_first=False
            )
            for i in xrange(5):
                if sch_proxy.apply() == 1:
                    break
                time.sleep(6)

            self.assertEqual(sch_proxy.apply(), 1)

            # TODO -> KVM doesn't restart itself
            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            ips_collected = sch_member.ip_list

            response_body = {}
            for i in xrange(20):
                try:
                    endpoint = "http://%s:2379/v2/members" % ips_collected[0]
                    request = urllib2.urlopen(endpoint)
                    response_body = json.loads(request.read())
                    request.close()
                    if len(response_body["members"]) == sch_member.etcd_members_nb:
                        break
                except urllib2.URLError:
                    pass

                time.sleep(6)

            self.assertEqual(len(response_body["members"]), sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_proxy.ip_list)

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
    # @unittest.skip("just skip")
    def test_05(self):
        self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
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
                time.sleep(3)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )

            time.sleep(20)
            for i in xrange(30):
                if sch_member.apply() is True:
                    break
                time.sleep(6)

            self.assertTrue(sch_member.apply())
            sch_proxy = scheduler.EtcdProxyScheduler(
                etcd_member_instance=sch_member,
                ignition_proxy="%s-emember" % marker,
                apply_first=False
            )
            for i in xrange(10):
                if sch_proxy.apply() == 2:
                    break
                time.sleep(6)

            self.assertEqual(sch_proxy.apply(), 2)

            # TODO -> KVM doesn't restart itself
            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            ips_collected = sch_member.ip_list

            response_body = {}
            for i in xrange(20):
                try:
                    endpoint = "http://%s:2379/v2/members" % ips_collected[0]
                    request = urllib2.urlopen(endpoint)
                    response_body = json.loads(request.read())
                    request.close()
                    if len(response_body["members"]) == sch_member.etcd_members_nb:
                        break
                except urllib2.URLError:
                    pass

                time.sleep(6)

            self.assertEqual(len(response_body["members"]), sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_proxy.ip_list)

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
    # @unittest.skip("just skip")
    def test_06(self):
        self.assertIsNone(self.fetch_discovery_interfaces()["interfaces"])
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
                time.sleep(4)  # KVM fail to associate nic

            sch_member = scheduler.EtcdMemberScheduler(
                api_endpoint=self.api_endpoint,
                bootcfg_path=self.test_bootcfg_path,
                ignition_member="%s-emember" % marker,
                bootcfg_prefix="%s-" % marker
            )
            sch_member.etcd_members_nb = 1

            time.sleep(20)
            for i in xrange(30):
                if sch_member.apply() is True:
                    break
                time.sleep(6)

            self.assertTrue(sch_member.apply())
            sch_proxy = scheduler.EtcdProxyScheduler(
                etcd_member_instance=sch_member,
                ignition_proxy="%s-emember" % marker,
                apply_first=False
            )
            for i in xrange(30):
                if sch_proxy.apply() == 4:
                    break
                time.sleep(6)

            self.assertEqual(sch_proxy.apply(), 4)

            # TODO -> KVM doesn't restart itself
            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            ips_collected = sch_member.ip_list

            response_body = {}
            for i in xrange(20):
                try:
                    endpoint = "http://%s:2379/v2/members" % ips_collected[0]
                    request = urllib2.urlopen(endpoint)
                    response_body = json.loads(request.read())
                    request.close()
                    if len(response_body["members"]) == sch_member.etcd_members_nb:
                        break
                except urllib2.URLError:
                    pass

                time.sleep(6)

            self.assertEqual(len(response_body["members"]), sch_member.etcd_members_nb)
            self.etcd_endpoint_health(sch_proxy.ip_list)

        finally:
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


if __name__ == "__main__":
    unittest.main()
