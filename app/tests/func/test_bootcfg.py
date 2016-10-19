import httplib
import json
import os
import urllib2
from unittest import TestCase
from multiprocessing import Process
import subprocess

import time

from app import generator


class TestBootConfigBasic(TestCase):
    p_bootcfg = Process
    gen = generator.Generator

    func_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path
    assets_path = "%s/bootcfg/assets" % project_path

    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    bootcfg_address = "0.0.0.0:8080"
    bootcfg_endpoint = "http://localhost:8080"

    @staticmethod
    def process_target():
        cmd = [
            "%s/bin/bootcfg" % TestBootConfigBasic.tests_path,
            "-data-path", "%s" % TestBootConfigBasic.test_bootcfg_path,
            "-assets-path", "%s" % TestBootConfigBasic.assets_path,
            "-address", "%s" % TestBootConfigBasic.bootcfg_address
        ]
        print " ".join(cmd)
        os.execv(cmd[0], cmd)

    @classmethod
    def setUpClass(cls):

        cls.clean_sandbox()

        subprocess.check_output(["make"], cwd=cls.project_path)
        cls.p_bootcfg = Process(target=TestBootConfigBasic.process_target)
        cls.p_bootcfg.start()
        assert cls.p_bootcfg.is_alive() is True

        marker = "%s" % cls.__name__.lower()
        ignition_file = "func-%s.yaml" % marker
        cls.gen = generator.Generator(_id="id-%s" % marker,
                                      name="name-%s" % marker,
                                      ignition_id=ignition_file,
                                      bootcfg_path=cls.test_bootcfg_path)
        cls.gen.dumps()

    @classmethod
    def tearDownClass(cls):
        print "\nSIGTERM -> %d" % cls.p_bootcfg.pid
        cls.p_bootcfg.terminate()
        cls.p_bootcfg.join(timeout=5)
        cls.clean_sandbox()

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestBootConfigBasic.test_bootcfg_path, k) for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_bootcfg.is_alive())
        self.assertEqual(self.gen.group.ip_address, self.gen.profile.ip_address)

    def test_00_bootcfg_running(self):
        response_body = ""
        response_code = 404
        for i in xrange(100):
            try:
                request = urllib2.urlopen(self.bootcfg_endpoint)
                response_body = request.read()
                response_code = request.code
                request.close()
                break

            except httplib.BadStatusLine:
                time.sleep(0.01)

            except urllib2.URLError:
                time.sleep(0.01)

        self.assertEqual("bootcfg\n", response_body)
        self.assertEqual(200, response_code)

    def test_01_bootcfg_ipxe(self):

        request = urllib2.urlopen("%s/ipxe" % self.bootcfg_endpoint)
        response = request.read()
        request.close()

        response = response.replace(" \n", "\n")
        lines = response.split("\n")

        shebang = lines[0]
        self.assertEqual(shebang, "#!ipxe")

        kernel = lines[1].split(" ")
        kernel_expect = [
            'kernel',
            '/assets/coreos/serve/coreos_production_pxe.vmlinuz',
            'coreos.autologin',
            'coreos.config.url=http://%s:8080/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}' % self.gen.group.ip_address,
            'coreos.first_boot']
        self.assertEqual(kernel, kernel_expect)

        init_rd = lines[2].split(" ")
        init_rd_expect = ['initrd', '/assets/coreos/serve/coreos_production_pxe_image.cpio.gz']
        self.assertEqual(init_rd, init_rd_expect)

        boot = lines[3]
        self.assertEqual(boot, "boot")

    def test_02_bootcfg_ignition(self):
        request = urllib2.urlopen("%s/ignition" % self.bootcfg_endpoint)
        response = request.read()
        request.close()

        ign_resp = json.loads(response)
        expect = {
            u'networkd': {},
            u'passwd': {},
            u'systemd': {},
            u'storage': {
                u'files': [{
                    u'group': {},
                    u'user': {},
                    u'filesystem':
                        u'root',
                    u'path': u'/tmp/hello',
                    u'contents': {
                        u'source': u'data:,Hello%20World%0A',
                        u'verification': {}
                    },
                    u'mode': 420}
                ]
            },
            u'ignition': {u'version': u'2.0.0', u'config': {}}}
        self.assertEqual(ign_resp, expect)
