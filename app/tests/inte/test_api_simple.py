import httplib
import json
import os
import shutil
import sys
import time
import unittest
import urllib2
from multiprocessing import Process

from app import api
from app import configs
from app import generator
from app import model
from common import posts

ec = configs.EnjoliverConfig(importer=__file__)


class TestAPI(unittest.TestCase):
    p_matchbox = Process

    int_path = "%s" % os.path.dirname(__file__)
    dbs_path = "%s/dbs" % int_path
    tests_path = "%s" % os.path.dirname(int_path)
    app_path = os.path.dirname(tests_path)
    project_path = os.path.dirname(app_path)
    matchbox_path = "%s/matchbox" % project_path
    assets_path = "%s/matchbox/assets" % project_path

    test_matchbox_path = "%s/test_matchbox" % tests_path

    @staticmethod
    def process_target_matchbox():
        os.environ["ENJOLIVER_MATCHBOX_PATH"] = TestAPI.test_matchbox_path
        os.environ["ENJOLIVER_MATCHBOX_ASSETS"] = TestAPI.assets_path
        cmd = [
            "%s/manage.py" % TestAPI.project_path,
            "matchbox",
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (
                     os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)

    @classmethod
    def setUpClass(cls):
        time.sleep(0.1)
        try:
            os.remove(ec.db_path)
        except OSError:
            pass
        engine = api.create_engine(ec.db_uri)
        model.Base.metadata.create_all(engine)
        api.engine = engine
        api.cache.clear()

        shutil.rmtree(ec.ignition_journal_dir, ignore_errors=True)

        cls.app = api.app.test_client()
        cls.app.testing = True

        cls.p_matchbox = Process(target=TestAPI.process_target_matchbox)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_matchbox.start()
        assert cls.p_matchbox.is_alive() is True

        cls.matchbox_running(ec.matchbox_uri, cls.p_matchbox)

    @classmethod
    def tearDownClass(cls):
        os.write(1, "TERM -> %d\n" % cls.p_matchbox.pid)
        sys.stdout.flush()
        cls.p_matchbox.terminate()
        cls.p_matchbox.join(timeout=5)
        time.sleep(0.2)

    @staticmethod
    def matchbox_running(matchbox_endpoint, p_matchbox):
        response_body = ""
        response_code = 404
        for i in xrange(10):
            assert p_matchbox.is_alive() is True
            try:
                request = urllib2.urlopen(matchbox_endpoint)
                response_body = request.read()
                response_code = request.code
                request.close()
                break

            except (httplib.BadStatusLine, urllib2.URLError):
                pass
            time.sleep(0.2)

        assert "matchbox\n" == response_body
        assert 200 == response_code

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (
            TestAPI.test_matchbox_path, k) for k in (
                    "profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_matchbox.is_alive())
        self.clean_sandbox()
        api.cache.clear()

    def test_00_healthz(self):
        expect = {
            u'flask': True,
            u'global': True,
            u'db': True,
            u'matchbox': {
                u'/': True,
                u'/boot.ipxe': True,
                u'/boot.ipxe.0': True,
                u'/assets': True,
                u"/metadata": True
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
            "chain http://127.0.0.1:5000/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        result = self.app.get('/boot.ipxe')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, expect)

    def test_01_boot_ipxe_0(self):
        expect = \
            "#!ipxe\n" \
            "echo start /boot.ipxe\n" \
            ":retry_dhcp\n" \
            "dhcp || goto retry_dhcp\n" \
            "chain http://127.0.0.1:5000/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        result = self.app.get('/boot.ipxe.0')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, expect)

    def test_02_root(self):
        self.maxDiff = None
        result = self.app.get('/')
        content = json.loads(result.data)
        self.assertEqual(result.status_code, 200)

    def test_03_ipxe_404(self):
        result = self.app.get('/ipxe')
        self.assertEqual(result.data, "404")
        self.assertEqual(result.status_code, 404)

    def test_04_ipxe(self):
        marker = "%s-%s" % (TestAPI.__name__.lower(), self.test_04_ipxe.__name__)
        ignition_file = "inte-%s.yaml" % marker
        gen = generator.Generator(
            api_uri=ec.api_uri,
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            matchbox_path=self.test_matchbox_path)
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
                 "boot\n" % (gen.profile.api_uri, gen.profile.api_uri, gen.profile.api_uri)
        self.assertEqual(result.data, expect)
        self.assertEqual(result.status_code, 200)

    def test_05_ipxe_selector(self):
        mac = "00:00:00:00:00:00"
        marker = "%s-%s" % (TestAPI.__name__.lower(), self.test_05_ipxe_selector.__name__)
        ignition_file = "inte-%s.yaml" % marker
        gen = generator.Generator(
            api_uri=ec.api_uri,
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            selector={"mac": mac},
            matchbox_path=self.test_matchbox_path
        )
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
                 "boot\n" % (gen.profile.api_uri, gen.profile.api_uri, gen.profile.api_uri)
        self.assertEqual(result.data, expect)
        self.assertEqual(result.status_code, 200)

    def test_06_discovery_400(self):
        result = self.app.post('/discovery', data="ok")
        self.assertEqual(result.status_code, 406)

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
             u'cidrv4': u'172.20.0.65/21',
             "gateway": "172.20.0.1"},

            {u'name': u'eth0',
             u'as_boot': True,
             u'machine': u'a21a9123-302d-488d-976c-5d6ded84a32d',
             'chassis_name': u'rkt-fe037484-d9c1-4f73-be5e-2c6a7b622fb4',
             u'netmask': 21,
             u'mac': u'52:54:00:a5:24:f5',
             u'ipv4': u'172.20.0.51',
             u'cidrv4': u'172.20.0.51/21',
             "gateway": "172.20.0.1"}
        ]
        result_data = json.loads(result.data)
        self.assertEqual(expect, result_data)

    def test_07_404_fake(self):
        result = self.app.get('/fake')
        self.assertEqual(result.status_code, 404)
