import httplib
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
import urllib2
from multiprocessing import Process

from app import api
from app import model
from app import generator
from common import posts


class TestAPI(unittest.TestCase):
    p_bootcfg = Process

    int_path = "%s" % os.path.dirname(__file__)
    dbs_path = "%s/dbs" % int_path
    tests_path = "%s" % os.path.dirname(int_path)
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

    @staticmethod
    def process_target():
        cmd = [
            "%s" % TestAPI.bootcfg_bin,
            "-data-path", "%s" % TestAPI.test_bootcfg_path,
            "-assets-path", "%s" % TestAPI.assets_path,
            "-address", "%s" % TestAPI.bootcfg_address,
            "-log-level", "debug"
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (
                     os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execv(cmd[0], cmd)

    @classmethod
    def setUpClass(cls):
        time.sleep(0.1)
        db_path = "%s/%s.sqlite" % (cls.dbs_path, TestAPI.__name__.lower())
        journal = "%s/ignition_journal" % cls.int_path
        db = "sqlite:///%s" % db_path
        try:
            os.remove(db_path)
        except OSError:
            pass
        engine = api.create_engine(db)
        model.Base.metadata.create_all(engine)
        api.engine = engine
        api.cache.clear()
        api.application.config["API_URI"] = "http://localhost"
        api.application.config["BOOTCFG_URI"] = cls.bootcfg_uri

        assert os.path.isfile(db_path)

        try:
            shutil.rmtree(journal)
        except OSError:
            pass

        assert os.path.isdir(journal) is False
        api.ignition_journal = journal
        cls.app = api.app.test_client()
        cls.app.testing = True

        # subprocess.check_output(["make"], cwd=cls.project_path)
        if os.path.isfile("%s" % TestAPI.bootcfg_bin) is False:
            raise IOError("%s" % TestAPI.bootcfg_bin)
        cls.p_bootcfg = Process(target=TestAPI.process_target)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_bootcfg.start()
        assert cls.p_bootcfg.is_alive() is True

        cls.bootcfg_running(cls.bootcfg_uri, cls.p_bootcfg)

    @classmethod
    def tearDownClass(cls):
        os.write(1, "TERM -> %d\n" % cls.p_bootcfg.pid)
        sys.stdout.flush()
        cls.p_bootcfg.terminate()
        cls.p_bootcfg.join(timeout=5)
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
    def clean_sandbox():
        dirs = ["%s/%s" % (
            TestAPI.test_bootcfg_path, k) for k in (
                    "profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_bootcfg.is_alive())
        self.clean_sandbox()
        api.cache.clear()

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
        result = self.app.get('/healthz')
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.data)
        self.assertEqual(expect, content)

    def test_01_boot_ipxe(self):
        expect = \
            "#!ipxe\n" \
            "echo start /boot.ipxe\n" \
            ":retry_dhcp\n" \
            "dhcp || goto retry_dhcp\n" \
            "chain http://localhost/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        result = self.app.get('/boot.ipxe')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, expect)

    def test_01_boot_ipxe_0(self):
        expect = \
            "#!ipxe\n" \
            "echo start /boot.ipxe\n" \
            ":retry_dhcp\n" \
            "dhcp || goto retry_dhcp\n" \
            "chain http://localhost/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        result = self.app.get('/boot.ipxe.0')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, expect)

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
            u'/ipxe'
        ]
        result = self.app.get('/')
        content = json.loads(result.data)
        self.assertEqual(result.status_code, 200)
        self.assertItemsEqual(content, expect)

    def test_03_ipxe_404(self):
        result = self.app.get('/ipxe')
        self.assertEqual(result.data, "404")
        self.assertEqual(result.status_code, 404)

    def test_04_ipxe(self):
        marker = "%s-%s" % (TestAPI.__name__.lower(), self.test_04_ipxe.__name__)
        ignition_file = "inte-%s.yaml" % marker
        gen = generator.Generator(
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            bootcfg_path=self.test_bootcfg_path)
        gen.dumps()
        result = self.app.get('/ipxe')
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
        self.assertEqual(result.data, expect)
        self.assertEqual(result.status_code, 200)

    def test_05_ipxe_selector(self):
        mac = "00:00:00:00:00:00"
        marker = "%s-%s" % (TestAPI.__name__.lower(), self.test_05_ipxe_selector.__name__)
        ignition_file = "inte-%s.yaml" % marker
        gen = generator.Generator(
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            selector={"mac": mac},
            bootcfg_path=self.test_bootcfg_path)
        gen.dumps()
        result = self.app.get('/ipxe')
        self.assertEqual(result.data, "404")
        self.assertEqual(result.status_code, 404)

        result = self.app.get('/ipxe?mac=%s' % mac)
        expect = "#!ipxe\n" \
                 "echo start /ipxe\n" \
                 "kernel %s/assets/coreos/serve/coreos_production_pxe.vmlinuz " \
                 "coreos.autologin coreos.config.url=%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp} " \
                 "coreos.first_boot coreos.oem.id=pxe\n" \
                 "initrd %s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz \n" \
                 "boot\n" % (gen.profile.bootcfg_uri, gen.profile.bootcfg_uri, gen.profile.bootcfg_uri)
        self.assertEqual(result.data, expect)
        self.assertEqual(result.status_code, 200)

    def test_06_discovery_400(self):
        result = self.app.post('/discovery', data="ok")
        self.assertEqual(result.status_code, 400)

    def test_06_discovery(self):
        result = self.app.get("/discovery/interfaces")
        self.assertEqual(json.loads(result.data), [])

    def test_06_discovery_00(self):
        result = self.app.post('/discovery', data=json.dumps(posts.M01),
                               content_type='application/json')
        self.assertEqual(json.loads(result.data), {u'total_elt': 1, u'new': True})
        self.assertEqual(result.status_code, 200)

    def test_06_discovery_01(self):
        result = self.app.post('/discovery', data=json.dumps(posts.M02),
                               content_type='application/json')
        self.assertEqual(json.loads(result.data), {u'total_elt': 2, u'new': True})
        self.assertEqual(result.status_code, 200)

        result = self.app.post('/discovery', data=json.dumps(posts.M02),
                               content_type='application/json')
        self.assertEqual(json.loads(result.data), {u'total_elt': 2, u'new': False})
        self.assertEqual(result.status_code, 200)

        result = self.app.get("/discovery/interfaces")
        expect = [
            {u'name': u'eth0',
             u'as_boot': True,
             u'netmask': 21,
             u'mac': u'52:54:00:e8:32:5b',
             u'ipv4': u'172.20.0.65',
             u'machine': u'b7f5f93a-b029-475f-b3a4-479ba198cb8a',
             'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             u'cidrv4': u'172.20.0.65/21'},

            {u'name': u'eth0',
             u'as_boot': True,
             u'machine': u'a21a9123-302d-488d-976c-5d6ded84a32d',
             'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             u'netmask': 21,
             u'mac': u'52:54:00:a5:24:f5',
             u'ipv4': u'172.20.0.51',
             u'cidrv4': u'172.20.0.51/21'}
        ]
        result_data = json.loads(result.data)
        self.assertEqual(expect, result_data)

    def test_07_404_fake(self):
        result = self.app.get('/fake')
        self.assertEqual(result.status_code, 404)
