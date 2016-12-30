import httplib
import json
import math
import os
import shutil
import subprocess
import sys
import time
import unittest
import urllib2
from multiprocessing import Process

import requests

from app import api
from app import generator
from app import model
from common import posts


class TestAPIAdvanced(unittest.TestCase):
    p_bootcfg = Process
    p_api = Process

    inte_path = "%s" % os.path.dirname(__file__)
    dbs_path = "%s/dbs" % inte_path
    tests_path = "%s" % os.path.dirname(inte_path)
    app_path = os.path.dirname(tests_path)
    project_path = os.path.dirname(app_path)
    bootcfg_path = "%s/bootcfg" % project_path
    assets_path = "%s/bootcfg/assets" % project_path

    runtime_path = "%s/runtime" % project_path
    rkt_bin = "%s/rkt/rkt" % runtime_path
    bootcfg_bin = "%s/bootcfg/bootcfg" % runtime_path

    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    bootcfg_port = int(os.getenv("BOOTCFG_PORT", "8080"))

    bootcfg_address = "0.0.0.0:%d" % bootcfg_port
    bootcfg_uri = "http://localhost:%d" % bootcfg_port

    api_port = int(os.getenv("API_PORT", "5000"))

    api_address = "0.0.0.0:%d" % api_port
    api_uri = "http://localhost:%d" % api_port

    @staticmethod
    def process_target_bootcfg():
        cmd = [
            "%s" % TestAPIAdvanced.bootcfg_bin,
            "-data-path", "%s" % TestAPIAdvanced.test_bootcfg_path,
            "-assets-path", "%s" % TestAPIAdvanced.assets_path,
            "-address", "%s" % TestAPIAdvanced.bootcfg_address,
            "-log-level", "debug"
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (
                     os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execv(cmd[0], cmd)

    @staticmethod
    def process_target_api():
        api.cache.clear()
        api.application.config["API_IP_PORT"] = "localhost:5000"
        api.app.run(host="localhost", port=TestAPIAdvanced.api_port)

    @classmethod
    def setUpClass(cls):
        time.sleep(0.1)
        db_path = "%s/%s.sqlite" % (cls.dbs_path, TestAPIAdvanced.__name__.lower())
        db = "sqlite:///%s" % db_path
        journal = "%s/ignition_journal" % cls.inte_path
        try:
            os.remove(db_path)
        except OSError:
            pass

        try:
            shutil.rmtree(journal)
        except OSError:
            pass

        assert os.path.isdir(journal) is False
        engine = api.create_engine(db)
        api.app.config["DB_PATH"] = db_path
        api.app.config["API_URI"] = cls.api_uri
        api.app.config["BOOTCFG_URI"] = cls.bootcfg_uri
        model.Base.metadata.create_all(engine)
        assert os.path.isfile(db_path)
        api.engine = engine

        # subprocess.check_output(["make"], cwd=cls.project_path)
        if os.path.isfile("%s" % TestAPIAdvanced.bootcfg_bin) is False:
            raise IOError("%s" % TestAPIAdvanced.bootcfg_bin)
        cls.p_bootcfg = Process(target=TestAPIAdvanced.process_target_bootcfg)
        cls.p_api = Process(target=TestAPIAdvanced.process_target_api)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_bootcfg.start()
        assert cls.p_bootcfg.is_alive() is True
        cls.p_api.start()
        assert cls.p_api.is_alive() is True

        cls.bootcfg_running(cls.bootcfg_uri, cls.p_bootcfg)
        cls.api_running(cls.api_uri, cls.p_api)

    @classmethod
    def tearDownClass(cls):
        os.write(1, "TERM -> %d\n" % cls.p_bootcfg.pid)
        sys.stdout.flush()
        cls.p_bootcfg.terminate()
        cls.p_bootcfg.join(timeout=5)
        cls.p_api.terminate()
        cls.p_api.join(timeout=5)
        time.sleep(0.1)

    @staticmethod
    def bootcfg_running(bootcfg_endpoint, p_bootcfg):
        response_body = ""
        response_code = 404
        for i in xrange(100):
            assert p_bootcfg.is_alive() is True
            try:
                request = urllib2.urlopen(bootcfg_endpoint)
                response_body = request.read()
                response_code = request.code
                request.close()
                break

            except httplib.BadStatusLine:
                time.sleep(0.5)

            except urllib2.URLError:
                time.sleep(0.5)

        assert "bootcfg\n" == response_body
        assert 200 == response_code

    @staticmethod
    def api_running(api_endpoint, p_api):
        response_code = 404
        for i in xrange(100):
            assert p_api.is_alive() is True
            try:
                request = urllib2.urlopen(api_endpoint)
                response_code = request.code
                request.close()
                break

            except httplib.BadStatusLine:
                time.sleep(0.5)

            except urllib2.URLError:
                time.sleep(0.5)

        assert 200 == response_code

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (
            TestAPIAdvanced.test_bootcfg_path, k) for k in (
                    "profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_bootcfg.is_alive())
        self.assertTrue(self.p_api.is_alive())
        self.clean_sandbox()

    def test_00_healthz(self):
        expect = {
            u'flask': True,
            u'global': True,
            u'bootcfg': {
                u'/': True,
                u'/boot.ipxe': True,
                u'/boot.ipxe.0': True,
                u'/assets': True
            }}
        request = urllib2.urlopen("%s/healthz" % self.api_uri)
        response_body = request.read()
        response_code = request.code
        request.close()
        self.assertEqual(json.loads(response_body), expect)
        self.assertEqual(200, response_code)

    def test_01_boot_ipxe(self):
        expect = \
            "#!ipxe\n" \
            "echo start /boot.ipxe\n" \
            ":retry_dhcp\n" \
            "dhcp || goto retry_dhcp\n" \
            "chain http://localhost:5000/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        request = urllib2.urlopen("%s/boot.ipxe" % self.api_uri)
        response_body = request.read()
        response_code = request.code
        request.close()
        self.assertEqual(response_code, 200)
        self.assertEqual(response_body, expect)

    def test_01_boot_ipxe_zero(self):
        expect = \
            "#!ipxe\n" \
            "echo start /boot.ipxe\n" \
            ":retry_dhcp\n" \
            "dhcp || goto retry_dhcp\n" \
            "chain http://localhost:5000/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        request = urllib2.urlopen("%s/boot.ipxe" % self.api_uri)
        response_body = request.read()
        response_code = request.code
        request.close()
        self.assertEqual(response_code, 200)
        self.assertEqual(response_body, expect)

    def test_02_root(self):
        expect = [
            u'/discovery',
            u'/discovery/interfaces',
            u'/discovery/ignition-journal/<string:uuid>',
            u'/discovery/ignition-journal/<string:uuid>/<string:boot_id>',
            u'/discovery/ignition-journal',
            u'/boot.ipxe',
            u'/boot.ipxe.0',
            u'/healthz',
            u'/backup/db',
            u'/',
            u'/ui',
            u'/ui/view/machine',
            u'/ipxe'
        ]
        request = urllib2.urlopen("%s/" % self.api_uri)
        response_body = request.read()
        response_code = request.code
        request.close()
        content = json.loads(response_body)
        self.assertEqual(response_code, 200)
        self.assertItemsEqual(content, expect)

    def test_03_ipxe_404(self):
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen("%s/404" % self.api_uri)

    def test_04_ipxe(self):
        marker = "%s-%s" % (TestAPIAdvanced.__name__.lower(), self.test_04_ipxe.__name__)
        ignition_file = "inte-%s.yaml" % marker
        gen = generator.Generator(
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            bootcfg_path=self.test_bootcfg_path)
        gen.dumps()
        request = urllib2.urlopen("%s/ipxe" % self.api_uri)
        response_body = request.read()
        response_code = request.code
        request.close()
        expect = "#!ipxe\n" \
                 "echo start /ipxe\n" \
                 "kernel " \
                 "%s/assets/coreos/serve/coreos_production_pxe.vmlinuz " \
                 "coreos.autologin " \
                 "coreos.config.url=%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp} " \
                 "coreos.first_boot " \
                 "coreos.oem.id=pxe\n" \
                 "initrd %s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz \n" \
                 "boot\n" % (gen.profile.bootcfg_uri, gen.profile.bootcfg_uri, gen.profile.bootcfg_uri)
        self.assertEqual(response_body, expect)
        self.assertEqual(response_code, 200)

    def test_05_ipxe_selector(self):
        mac = "00:00:00:00:00:00"
        marker = "%s-%s" % (TestAPIAdvanced.__name__.lower(), self.test_05_ipxe_selector.__name__)
        ignition_file = "inte-%s.yaml" % marker
        gen = generator.Generator(
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            selector={"mac": mac},
            bootcfg_path=self.test_bootcfg_path)
        gen.dumps()
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen("%s/ipxe" % self.api_uri)

        request = urllib2.urlopen("%s/ipxe?mac=%s" % (self.api_uri, mac))
        response_body = request.read()
        response_code = request.code
        request.close()
        expect = "#!ipxe\n" \
                 "echo start /ipxe\n" \
                 "kernel %s/assets/coreos/serve/coreos_production_pxe.vmlinuz " \
                 "coreos.autologin " \
                 "coreos.config.url=%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp} " \
                 "coreos.first_boot coreos.oem.id=pxe\n" \
                 "initrd %s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz \n" \
                 "boot\n" % (gen.profile.bootcfg_uri, gen.profile.bootcfg_uri, gen.profile.bootcfg_uri)
        self.assertEqual(response_body, expect)
        self.assertEqual(response_code, 200)

    def test_06_discovery_00(self):
        req = urllib2.Request("%s/discovery" % self.api_uri, json.dumps(posts.M01),
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = f.read()
        f.close()
        self.assertEqual(json.loads(response), {u'total_elt': 1, u'new': True})
        req = urllib2.Request("%s/discovery/interfaces" % self.api_uri)
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = json.loads(f.read())
        expect = [
            {
                "as_boot": True,
                "chassis_name": "rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4",
                "cidrv4": "172.20.0.65/21",
                "ipv4": "172.20.0.65",
                "mac": "52:54:00:e8:32:5b",
                "machine": "b7f5f93a-b029-475f-b3a4-479ba198cb8a",
                "name": "eth0",
                "netmask": 21
            }
        ]
        f.close()
        self.assertEqual(expect, response)

        req = urllib2.Request("%s/discovery" % self.api_uri)
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = json.loads(f.read())
        expect = [
            {
                u'boot-info': {
                    u'mac': u'52:54:00:e8:32:5b',
                    u'uuid': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a'
                },
                u'interfaces': [
                    {
                        u'name': u'eth0',
                        u'as_boot': True,
                        u'netmask': 21,
                        u'mac': u'52:54:00:e8:32:5b',
                        u'ipv4': u'172.20.0.65',
                        u'cidrv4': u'172.20.0.65/21'
                    }
                ]
            }
        ]
        f.close()
        self.assertEqual(expect, response)
        req = urllib2.Request("%s/discovery/ignition-journal/b7f5f93a-b029-475f-b3a4-479ba198cb8a" % self.api_uri)
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = json.loads(f.read())
        self.assertEqual(39, len(response))

    def test_06_discovery_01(self):
        req = urllib2.Request("%s/discovery" % self.api_uri, json.dumps(posts.M02),
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = f.read()
        f.close()
        self.assertEqual(json.loads(response), {u'total_elt': 2, u'new': True})

    def test_06_discovery_02(self):
        req = urllib2.Request("%s/discovery" % self.api_uri, json.dumps(posts.M03),
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = f.read()
        f.close()
        self.assertEqual(json.loads(response), {u'total_elt': 3, u'new': True})
        all_machines = urllib2.urlopen("%s/discovery" % self.api_uri)
        content = json.loads(all_machines.read())
        all_machines.close()

        req = urllib2.Request("%s/discovery" % self.api_uri, json.dumps(posts.M01),
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = f.read()
        f.close()
        self.assertEqual(json.loads(response), {u'total_elt': 3, u'new': False})
        self.assertEqual(posts.M01["boot-info"]["uuid"], content[0]["boot-info"]["uuid"])

    def test_06_discovery_03(self):
        """
        The db have already M01, M02, M03
        :return:
        """
        for i, p in enumerate(posts.ALL):
            req = urllib2.Request("%s/discovery" % self.api_uri, json.dumps(p),
                                  {'Content-Type': 'application/json'})
            f = urllib2.urlopen(req)
            self.assertEqual(200, f.code)
            response = f.read()
            f.close()
            pn = i + 1
            if pn == 1 or pn == 2 or pn == 3:
                self.assertEqual(json.loads(response), {u'total_elt': 3, u'new': False})
            else:
                self.assertEqual(json.loads(response), {u'total_elt': pn, u'new': True})

    def test_07_get(self):
        """
        Cache non regression
        """
        r = requests.get("%s/discovery" % self.api_uri)
        l = len(json.loads(r.content))
        r.close()
        self.assertEqual(l, len(posts.ALL))
        now = time.time()
        nb = 100
        for i in xrange(nb):
            r = requests.get("%s/discovery" % self.api_uri)
            r.close()
        self.assertTrue(now + (nb // 100) > time.time())
        r = requests.get("%s/discovery" % self.api_uri)
        l = len(json.loads(r.content))
        r.close()
        self.assertEqual(l, len(posts.ALL))

    def test_08_backup(self):
        n = int(math.floor(time.time()))
        r = requests.post("%s/backup/db" % self.api_uri)
        s = json.loads(r.content)
        r.close()
        self.assertTrue(s["copy"])
        self.assertTrue(os.path.isfile(s["dest_fs"]))
        os.remove(s["dest_fs"])
        self.assertTrue(n < s["ts"])
