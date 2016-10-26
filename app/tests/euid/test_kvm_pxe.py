import os
import unittest
import socket
from unittest import TestCase
from multiprocessing import Process
import subprocess

import sys

import time

from flask import Flask
from flask import request
from werkzeug.datastructures import ImmutableMultiDict

from app import generator


# from app import weback




@unittest.skipIf(os.geteuid() != 0,
                 "TestKVM need privilege")
class TestKVM(TestCase):
    p_bootcfg = Process
    p_dnsmasq = Process
    gen = generator.Generator

    func_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path
    assets_path = "%s/bootcfg/assets" % project_path

    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    bootcfg_port = int(os.getenv("BOOTCFG_PORT", "8080"))

    bootcfg_address = "0.0.0.0:%d" % bootcfg_port
    bootcfg_endpoint = "http://localhost:%d" % bootcfg_port

    @staticmethod
    def process_target_bootcfg():
        cmd = [
            "%s/bootcfg_dir/bootcfg" % TestKVM.tests_path,
            "-data-path", "%s" % TestKVM.test_bootcfg_path,
            "-assets-path", "%s" % TestKVM.assets_path,
            "-address", "%s" % TestKVM.bootcfg_address,
            "-log-level", "debug"
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execv(cmd[0], cmd)

    @staticmethod
    def process_target_dnsmasq():
        cmd = [
            "%s/rkt_dir/rkt" % TestKVM.tests_path,
            "--debug",
            "--dir=%s/rkt_dir/data" % TestKVM.tests_path,
            "--local-config=%s" % TestKVM.tests_path,
            "--mount",
            "volume=config,target=/etc/dnsmasq.conf",
            "run",
            "quay.io/coreos/dnsmasq:v0.3.0",
            "--insecure-options=all",
            "--net=host",
            "--interactive",
            "--uuid-file-save=/tmp/dnsmasq.uuid",
            "--volume",
            "config,kind=host,source=%s/dnsmasq-metal0.conf" % TestKVM.tests_path
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execv(cmd[0], cmd)
        os._exit(2)

    @staticmethod
    def process_target_create_metal0():
        cmd = [
            "%s/rkt_dir/rkt" % TestKVM.tests_path,
            "--debug",
            "--dir=%s/rkt_dir/data" % TestKVM.tests_path,
            "--local-config=%s" % TestKVM.tests_path,
            "run",
            "quay.io/coreos/dnsmasq:v0.3.0",
            "--insecure-options=all",
            "--net=metal0",
            "--interactive",
            "--exec",
            "/bin/true"]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execv(cmd[0], cmd)
        os._exit(2)  # Should not happen

    @staticmethod
    def dns_masq_running():
        """
        net.d/10-metal0.conf
        {
            "name": "metal0",
            "type": "bridge",
            "bridge": "metal0",
            "isGateway": true,
            "ipMasq": true,
            "ipam": {
                "type": "host-local",
                "subnet": "172.15.0.0/16",
                "routes" : [ { "dst" : "0.0.0.0/0" } ]
            }
        }
        :return:
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = 1
        for i in xrange(120):
            result = sock.connect_ex(('172.15.0.1', 53))
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

        if os.path.isfile("%s/rkt_dir/rkt" % TestKVM.tests_path) is False or \
                        os.path.isfile("%s/bootcfg_dir/bootcfg" % TestKVM.tests_path) is False:
            os.write(2, "Call 'make' as user for:\n"
                        "- %s/rkt_dir/rkt\n" % TestKVM.tests_path +
                     "- %s/bootcfg_dir/bootcfg\n" % TestKVM.tests_path)
            exit(2)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_bootcfg = Process(target=TestKVM.process_target_bootcfg)
        cls.p_bootcfg.start()
        assert cls.p_bootcfg.is_alive() is True

        if subprocess.call(["ip", "link", "show", "metal0"], stdout=None) != 0:
            p_create_metal0 = Process(
                target=TestKVM.process_target_create_metal0)
            p_create_metal0.start()
            for i in xrange(60):
                if p_create_metal0.exitcode == 0:
                    os.write(1, "Bridge done\n\r")
                    break
                os.write(1, "Bridge not ready\n\r")
                time.sleep(0.5)
        assert subprocess.call(["ip", "link", "show", "metal0"]) == 0

        cls.p_dnsmasq = Process(target=TestKVM.process_target_dnsmasq)
        cls.p_dnsmasq.start()
        assert cls.p_dnsmasq.is_alive() is True
        TestKVM.dns_masq_running()
        # cls.generator()

    @classmethod
    def tearDownClass(cls):
        os.write(1, "\n\rTERM -> %d\n\r" % cls.p_bootcfg.pid)
        sys.stdout.flush()
        cls.p_bootcfg.terminate()
        cls.p_bootcfg.join(timeout=5)
        cls.p_dnsmasq.terminate()
        cls.p_dnsmasq.join(timeout=5)
        # cls.clean_sandbox()
        subprocess.call([
            "%s/rkt_dir/rkt" % TestKVM.tests_path,
            "--debug",
            "--dir=%s/rkt_dir/data" % TestKVM.tests_path,
            "--local-config=%s" % TestKVM.tests_path,
            "gc",
            "--grace-period=0s"])

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestKVM.test_bootcfg_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_bootcfg.is_alive())
        self.assertTrue(self.p_dnsmasq.is_alive())

    @staticmethod
    def virsh(cmd, assertion=False):
        os.write(1, "\n\r-> " + " ".join(cmd) + "\n\r")
        sys.stdout.flush()
        ret = subprocess.call(cmd)
        if assertion is True and ret != 0:
            raise RuntimeError("\"%s\"" % " ".join(cmd))

    def test_00(self):
        marker = "euid-%s-%s" % (TestKVM.__name__.lower(), self.test_00.__name__)
        os.environ["BOOTCFG_IP"] = "172.15.0.1"
        gen = generator.Generator(
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            bootcfg_path=self.test_bootcfg_path
        )
        gen.dumps()

        app = Flask(marker)
        resp = []

        @app.route('/discovery', methods=['POST'])
        def root():
            resp.append(request.form)
            request.environ.get('werkzeug.server.shutdown')()
            return ""

        destroy, undefine = ["virsh", "destroy", "%s" % marker], ["virsh", "undefine", "%s" % marker]
        self.virsh(destroy), self.virsh(undefine)

        try:
            virt_install = [
                "virt-install",
                "--name",
                "%s" % marker,
                "--network=bridge:metal0",
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
            app.run(
                host="172.15.0.1", port=5000, debug=False, use_reloader=False)

        finally:
            self.virsh(destroy)
            self.virsh(undefine)
        self.assertEqual(resp, [ImmutableMultiDict([('euid-testkvm-test_00', u'')])])


if __name__ == "__main__":
    unittest.main()
