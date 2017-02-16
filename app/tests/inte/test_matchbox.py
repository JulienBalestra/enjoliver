import httplib
import json
import os
import urllib2
from unittest import TestCase
from multiprocessing import Process
import subprocess

import time

import sys

from app import generator


class IOErrorToWarning(object):
    def __enter__(self):
        generator.GenerateCommon._raise_enof = Warning

    def __exit__(self, ext, exv, trb):
        generator.GenerateCommon._raise_enof = IOError


class TestBootConfigCommon(TestCase):
    p_matchbox = Process
    gen = generator.Generator

    func_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    matchbox_path = "%s/matchbox" % project_path
    assets_path = "%s/matchbox/assets" % project_path

    runtime_path = "%s/runtime" % project_path
    rkt_bin = "%s/rkt/rkt" % runtime_path
    matchbox_bin = "%s/matchbox/matchbox" % runtime_path

    test_matchbox_path = "%s/test_matchbox" % tests_path

    matchbox_port = int(os.getenv("MATCHBOX_PORT", "8080"))

    # matchbox_address = "0.0.0.0:%d" % matchbox_port
    matchbox_endpoint = "http://localhost:%d" % matchbox_port

    api_uri = "http://127.0.0.1:5000"

    @staticmethod
    def process_target():
        cmd = [
            "%s" % TestBootConfigCommon.matchbox_bin,
            "-data-path", "%s" % TestBootConfigCommon.test_matchbox_path,
            "-assets-path", "%s" % TestBootConfigCommon.assets_path,
            # "-address", "%s" % TestBootConfigCommon.matchbox_address,
            "-log-level", "debug"
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (
                     os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execv(cmd[0], cmd)

    @classmethod
    def generator(cls):
        marker = "%s" % cls.__name__.lower()
        ignition_file = "inte-%s.yaml" % marker
        try:
            cls.gen = generator.Generator(
                api_uri=cls.api_uri,
                profile_id="id-%s" % marker,
                name="name-%s" % marker,
                ignition_id=ignition_file,
                matchbox_path=cls.test_matchbox_path
            )
        except IOError:
            os.write(2,
                     "\nWARNING %s override %s in %s\n" %
                     (cls.__name__,
                      generator.GenerateCommon._raise_enof,
                      Warning))
            sys.stderr.flush()
            with IOErrorToWarning():
                cls.gen = generator.Generator(
                    api_uri=cls.api_uri,
                    profile_id="id-%s" % marker,
                    name="name-%s" % marker,
                    ignition_id=ignition_file,
                    matchbox_path=cls.test_matchbox_path
                )

        cls.gen.dumps()

    @classmethod
    def setUpClass(cls):
        time.sleep(0.1)
        cls.clean_sandbox()
        os.environ["API_URI"] = cls.api_uri

        subprocess.check_output(["make"], cwd=cls.project_path)
        if os.path.isfile("%s" % TestBootConfigCommon.matchbox_bin) is False:
            raise IOError("%s" % TestBootConfigCommon.matchbox_bin)
        cls.p_matchbox = Process(target=TestBootConfigCommon.process_target)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_matchbox.start()
        assert cls.p_matchbox.is_alive() is True

        cls.generator()
        cls.matchbox_running(cls.matchbox_endpoint, cls.p_matchbox)

    @classmethod
    def tearDownClass(cls):
        os.write(1, "TERM -> %d\n" % cls.p_matchbox.pid)
        sys.stdout.flush()
        cls.p_matchbox.terminate()
        cls.p_matchbox.join(timeout=5)
        cls.clean_sandbox()
        time.sleep(0.1)

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (
            TestBootConfigCommon.test_matchbox_path, k) for k in (
                    "profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_matchbox.is_alive())
        try:
            self.assertEqual(self.gen.group.api_uri, self.gen.profile.api_uri)
        except AttributeError:
            # gen not declared
            pass

    @staticmethod
    def matchbox_running(matchbox_endpoint, p_matchbox):
        response_body = ""
        response_code = 404
        for i in xrange(100):
            assert p_matchbox.is_alive() is True
            try:
                request = urllib2.urlopen(matchbox_endpoint)
                response_body = request.read()
                response_code = request.code
                request.close()
                break

            except httplib.BadStatusLine:
                time.sleep(0.5)

            except urllib2.URLError:
                time.sleep(0.5)

        assert "matchbox\n" == response_body
        assert 200 == response_code

    def test_01_boot_dot_ipxe(self):
        request = urllib2.urlopen("%s/boot.ipxe" % self.matchbox_endpoint)
        response = request.read()
        request.close()
        self.assertEqual(
            response,
            "#!ipxe\n"
            "chain ipxe?uuid=${uuid}&mac=${mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n")

    def test_02_ipxe(self):
        request = urllib2.urlopen("%s/ipxe" % self.matchbox_endpoint)
        response = request.read()
        request.close()

        response = response.replace(" \n", "\n")
        lines = response.split("\n")
        lines = [k for k in lines if k]

        shebang = lines[0]
        self.assertEqual(shebang, "#!ipxe")

        kernel = lines[1].split(" ")
        kernel_expect = [
            'kernel',
            '%s/assets/coreos/serve/coreos_production_pxe.vmlinuz' % self.gen.profile.api_uri,
            'coreos.autologin',
            'coreos.config.url=%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}' % self.gen.profile.api_uri,
            'coreos.first_boot',
            "coreos.oem.id=pxe"]
        self.assertEqual(kernel, kernel_expect)

        init_rd = lines[2].split(" ")
        init_rd_expect = ['initrd',
                          '%s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz' % self.gen.profile.api_uri]
        self.assertEqual(init_rd, init_rd_expect)

        boot = lines[3]
        self.assertEqual(boot, "boot")
        self.assertEqual(len(lines), 4)

    def test_03_assets(self):
        request = urllib2.urlopen("%s/assets" % self.matchbox_endpoint)
        request.close()
        self.assertEqual(200, request.code)

    def test_03_assets_coreos(self):
        request = urllib2.urlopen("%s/assets/coreos" % self.matchbox_endpoint)
        request.close()
        self.assertEqual(200, request.code)

    def test_03_assets_coreos_serve(self):
        request = urllib2.urlopen("%s/assets/coreos/serve" % self.matchbox_endpoint)
        request.close()
        self.assertEqual(200, request.code)

    def test_03_assets_coreos_serve_kernel(self):
        request = urllib2.urlopen("%s/assets/coreos/serve/coreos_production_pxe.vmlinuz" % self.matchbox_endpoint)
        request.close()
        self.assertEqual(200, request.code)

    def test_03_assets_coreos_serve_initrd(self):
        request = urllib2.urlopen("%s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz" % self.matchbox_endpoint)
        request.close()
        self.assertEqual(200, request.code)

    def test_03_assets_coreos_serve_404(self):
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen("%s/assets/coreos/serve/404_request.not-here" % self.matchbox_endpoint)


class TestBootConfigHelloWorld(TestBootConfigCommon):
    def test_a0_ignition(self):
        request = urllib2.urlopen("%s/ignition" % self.matchbox_endpoint)
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


class TestBootConfigSelector(TestBootConfigCommon):
    mac = "00:00:00:00:00:00"

    @classmethod
    def generator(cls):
        marker = "%s" % cls.__name__.lower()
        ignition_file = "inte-%s.yaml" % marker
        cls.gen = generator.Generator(
            api_uri=cls.api_uri,
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            selector={"mac": cls.mac},
            matchbox_path=cls.test_matchbox_path
        )
        cls.gen.dumps()

    def test_02_ipxe(self):
        request = urllib2.urlopen("%s/ipxe?mac=%s" % (self.matchbox_endpoint, self.mac))
        response = request.read()
        request.close()

        response = response.replace(" \n", "\n")
        lines = response.split("\n")
        lines = [k for k in lines if k]

        shebang = lines[0]
        self.assertEqual(shebang, "#!ipxe")

        kernel = lines[1].split(" ")
        kernel_expect = [
            'kernel',
            '%s/assets/coreos/serve/coreos_production_pxe.vmlinuz' % self.gen.profile.api_uri,
            'coreos.autologin',
            'coreos.config.url=%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}' % self.gen.profile.api_uri,
            'coreos.first_boot',
            "coreos.oem.id=pxe"]
        self.assertEqual(kernel, kernel_expect)

        init_rd = lines[2].split(" ")
        init_rd_expect = ['initrd',
                          '%s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz' % self.gen.profile.api_uri]
        self.assertEqual(init_rd, init_rd_expect)

        boot = lines[3]
        self.assertEqual(boot, "boot")
        self.assertEqual(len(lines), 4)

    def test_a1_ipxe_raise(self):
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen("%s/ipxe" % self.matchbox_endpoint)

    def test_a2_ipxe_raise(self):
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen("%s/ignition?mac=%s" % (self.matchbox_endpoint, "01:01:01:01:01:01"))

    def test_a0_ignition(self):
        request = urllib2.urlopen("%s/ignition?mac=%s" % (self.matchbox_endpoint, self.mac))
        response = request.read()
        request.close()

        ign_resp = json.loads(response)
        expect = {
            u'networkd': {},
            u'passwd': {},
            u'systemd': {},
            u'storage': {
                u'files': [
                    {
                        u'group': {},
                        u'user': {},
                        u'filesystem': u'root',
                        u'path': u'/tmp/selector',
                        u'contents': {
                            u'source': u'data:,BySelector%0A', u'verification': {}
                        },
                        u'mode': 420}]
            },
            u'ignition': {u'version': u'2.0.0', u'config': {}}}
        self.assertEqual(ign_resp, expect)


class TestBootConfigSelectors(TestBootConfigCommon):
    mac_one = "00:00:00:00:00:01"
    mac_two = "00:00:00:00:00:02"
    mac_three = "00:00:00:00:00:03"

    # @staticmethod
    # def clean_sandbox():
    #     # Don't clean
    #     pass

    @classmethod
    def generator(cls):
        marker_one = "%s-one" % cls.__name__.lower()
        ignition_file = "inte-%s.yaml" % marker_one
        gen_one = generator.Generator(
            api_uri=cls.api_uri,
            profile_id="id-%s" % marker_one,
            name="name-%s" % marker_one,
            ignition_id=ignition_file,
            selector={"mac": cls.mac_one},
            matchbox_path=cls.test_matchbox_path
        )
        gen_one.dumps()

        marker_two = "%s-two" % cls.__name__.lower()
        ignition_file = "inte-%s.yaml" % marker_two
        gen_one = generator.Generator(
            api_uri=cls.api_uri,
            profile_id="id-%s" % marker_two,
            name="name-%s" % marker_two,
            ignition_id=ignition_file,
            selector={"mac": cls.mac_two},
            matchbox_path=cls.test_matchbox_path
        )
        gen_one.dumps()

        marker_three = "%s-three" % cls.__name__.lower()
        ignition_file = "inte-testbootconfigselectors-default.yaml"
        gen_one = generator.Generator(
            api_uri=cls.api_uri,
            profile_id="id-%s" % marker_three,
            name="name-%s" % marker_three,
            ignition_id=ignition_file,
            matchbox_path=cls.test_matchbox_path
        )
        gen_one.dumps()

    def test_ignition_1(self):
        request = urllib2.urlopen("%s/ignition?mac=%s" % (self.matchbox_endpoint, self.mac_one))
        response = request.read()
        request.close()

        ign_resp = json.loads(response)
        expect = {
            u'networkd': {},
            u'passwd': {},
            u'systemd': {},
            u'storage': {
                u'files': [
                    {
                        u'group': {},
                        u'user': {},
                        u'filesystem': u'root',
                        u'path': u'/tmp/selector',
                        u'contents': {
                            u'source': u'data:,BySelectorOne%0A', u'verification': {}
                        },
                        u'mode': 420}]
            },
            u'ignition': {u'version': u'2.0.0', u'config': {}}}
        self.assertEqual(ign_resp, expect)

    def test_ignition_2(self):
        request = urllib2.urlopen("%s/ignition?mac=%s" % (self.matchbox_endpoint, self.mac_two))
        response = request.read()
        request.close()

        ign_resp = json.loads(response)
        expect = {
            u'networkd': {},
            u'passwd': {},
            u'systemd': {},
            u'storage': {
                u'files': [
                    {
                        u'group': {},
                        u'user': {},
                        u'filesystem': u'root',
                        u'path': u'/tmp/selector',
                        u'contents': {
                            u'source': u'data:,BySelectorTwo%0A', u'verification': {}
                        },
                        u'mode': 420}]
            },
            u'ignition': {u'version': u'2.0.0', u'config': {}}}
        self.assertEqual(ign_resp, expect)

    def test_ignition_3(self):
        request = urllib2.urlopen("%s/ignition?mac=%s" % (self.matchbox_endpoint, self.mac_three))
        response = request.read()
        request.close()

        ign_resp = json.loads(response)
        expect = {
            u'networkd': {},
            u'passwd': {},
            u'systemd': {},
            u'storage': {
                u'files': [
                    {
                        u'group': {},
                        u'user': {},
                        u'filesystem': u'root',
                        u'path': u'/tmp/selector',
                        u'contents': {
                            u'source': u'data:,NoSelector%0A', u'verification': {}
                        },
                        u'mode': 420}]
            },
            u'ignition': {u'version': u'2.0.0', u'config': {}}}
        self.assertEqual(ign_resp, expect)
