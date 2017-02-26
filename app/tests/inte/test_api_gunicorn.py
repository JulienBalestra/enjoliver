import httplib
import json
import math
import os
import shutil
import sys
import time
import unittest
import urllib2
from multiprocessing import Process

import requests

from app import configs
from app import generator
from common import posts

ec = configs.EnjoliverConfig(importer=__file__)
ec.api_uri = "http://127.0.0.1:5000"


class TestAPIGunicorn(unittest.TestCase):
    p_matchbox = Process
    p_api = Process

    inte_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.dirname(inte_path)
    app_path = os.path.dirname(tests_path)
    project_path = os.path.dirname(app_path)
    assets_path = "%s/matchbox/assets" % project_path
    test_matchbox_path = "%s/test_matchbox" % tests_path

    @staticmethod
    def process_target_matchbox():
        os.environ["ENJOLIVER_MATCHBOX_PATH"] = TestAPIGunicorn.test_matchbox_path
        os.environ["ENJOLIVER_MATCHBOX_ASSETS"] = TestAPIGunicorn.assets_path
        cmd = [
            "%s/manage.py" % TestAPIGunicorn.project_path,
            "matchbox"
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (
                     os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def process_target_api():
        os.environ["ENJOLIVER_API_URI"] = ec.api_uri
        cmd = [
            "%s/manage.py" % TestAPIGunicorn.project_path,
            "gunicorn",
        ]
        os.execve(cmd[0], cmd, os.environ)

    @classmethod
    def setUpClass(cls):
        time.sleep(0.2)
        cls.clean_sandbox()
        try:
            os.remove(ec.db_path)
        except OSError:
            pass

        shutil.rmtree(ec.ignition_journal_dir, ignore_errors=True)

        cls.p_matchbox = Process(target=TestAPIGunicorn.process_target_matchbox)
        cls.p_api = Process(target=TestAPIGunicorn.process_target_api)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_matchbox.start()
        assert cls.p_matchbox.is_alive() is True
        cls.p_api.start()
        assert cls.p_api.is_alive() is True

        cls.matchbox_running(ec.matchbox_uri, cls.p_matchbox)
        cls.api_running(ec.api_uri, cls.p_api)

    @classmethod
    def tearDownClass(cls):
        os.write(1, "TERM -> %d\n" % cls.p_matchbox.pid)
        sys.stdout.flush()
        cls.p_matchbox.terminate()
        cls.p_matchbox.join(timeout=5)
        cls.p_api.terminate()
        cls.p_api.join(timeout=5)
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
    def api_running(api_endpoint, p_api):
        response_code = 404
        for i in xrange(10):
            assert p_api.is_alive() is True
            try:
                request = urllib2.urlopen(api_endpoint)
                response_code = request.code
                request.close()
                break

            except (httplib.BadStatusLine, urllib2.URLError):
                pass
            time.sleep(0.2)

        assert 200 == response_code

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestAPIGunicorn.test_matchbox_path, k) for k in (
            "profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.assertTrue(self.p_matchbox.is_alive())
        self.assertTrue(self.p_api.is_alive())
        self.clean_sandbox()

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
        request = urllib2.urlopen("%s/healthz" % ec.api_uri)
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
            "chain http://127.0.0.1:5000/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        request = urllib2.urlopen("%s/boot.ipxe" % ec.api_uri)
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
            "chain http://127.0.0.1:5000/ipxe?uuid=${uuid}&mac=${net0/mac:hexhyp}&domain=${domain}&hostname=${hostname}&serial=${serial}\n"
        request = urllib2.urlopen("%s/boot.ipxe" % ec.api_uri)
        response_body = request.read()
        response_code = request.code
        request.close()
        self.assertEqual(response_code, 200)
        self.assertEqual(response_body, expect)

    def test_02_root(self):
        request = urllib2.urlopen("%s/" % ec.api_uri)
        response_code = request.code
        request.close()
        self.assertEqual(response_code, 200)

    def test_03_ipxe_404(self):
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen("%s/404" % ec.api_uri)

    def test_04_ipxe(self):
        marker = "%s-%s" % (TestAPIGunicorn.__name__.lower(), self.test_04_ipxe.__name__)
        ignition_file = "inte-%s.yaml" % marker
        gen = generator.Generator(
            api_uri=ec.api_uri,
            profile_id="id-%s" % marker,
            name="name-%s" % marker,
            ignition_id=ignition_file,
            matchbox_path=self.test_matchbox_path
        )
        gen.dumps()
        request = urllib2.urlopen("%s/ipxe" % ec.api_uri)
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
                 "boot\n" % (gen.profile.api_uri, gen.profile.api_uri, gen.profile.api_uri)
        self.assertEqual(response_body, expect)
        self.assertEqual(response_code, 200)

    def test_05_ipxe_selector(self):
        mac = "00:00:00:00:00:00"
        marker = "%s-%s" % (TestAPIGunicorn.__name__.lower(), self.test_05_ipxe_selector.__name__)
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
        with self.assertRaises(urllib2.HTTPError):
            urllib2.urlopen("%s/ipxe" % ec.api_uri)

        request = urllib2.urlopen("%s/ipxe?mac=%s" % (ec.api_uri, mac))
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
                 "boot\n" % (gen.profile.api_uri, gen.profile.api_uri, gen.profile.api_uri)
        self.assertEqual(response_body, expect)
        self.assertEqual(response_code, 200)

    def test_06_discovery_00(self):
        req = urllib2.Request("%s/discovery" % ec.api_uri, json.dumps(posts.M01),
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = f.read()
        f.close()
        self.assertEqual(json.loads(response), {u'total_elt': 1, u'new': True})
        req = urllib2.Request("%s/discovery/interfaces" % ec.api_uri)
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
                "netmask": 21,
                "gateway": "172.20.0.1"
            }
        ]
        f.close()
        self.assertEqual(expect, response)

        req = urllib2.Request("%s/discovery" % ec.api_uri)
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = json.loads(f.read())
        expect = {
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
                    u'cidrv4': u'172.20.0.65/21',
                    "gateway": "172.20.0.1"
                }
            ]
        }

        f.close()
        self.assertEqual(1, len(response))
        first = response[0]
        self.assertEqual(first["boot-info"]["uuid"], expect["boot-info"]["uuid"])
        self.assertEqual(first["boot-info"]["mac"], expect["boot-info"]["mac"])
        self.assertEqual(first["interfaces"][0]["mac"], expect["interfaces"][0]["mac"])
        self.assertEqual(first["interfaces"][0]["as_boot"], expect["interfaces"][0]["as_boot"])

        req = urllib2.Request("%s/discovery/ignition-journal/b7f5f93a-b029-475f-b3a4-479ba198cb8a" % ec.api_uri)
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = json.loads(f.read())
        self.assertEqual(39, len(response))

    def test_06_discovery_01(self):
        req = urllib2.Request("%s/discovery" % ec.api_uri, json.dumps(posts.M02),
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = f.read()
        f.close()
        self.assertEqual(json.loads(response), {u'total_elt': 2, u'new': True})

    def test_06_discovery_02(self):
        req = urllib2.Request("%s/discovery" % ec.api_uri, json.dumps(posts.M03),
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.assertEqual(200, f.code)
        response = f.read()
        f.close()
        self.assertEqual(json.loads(response), {u'total_elt': 3, u'new': True})
        all_machines = urllib2.urlopen("%s/discovery" % ec.api_uri)
        content = json.loads(all_machines.read())
        all_machines.close()

        req = urllib2.Request("%s/discovery" % ec.api_uri, json.dumps(posts.M01),
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
            req = urllib2.Request("%s/discovery" % ec.api_uri, json.dumps(p),
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
        r = requests.get("%s/discovery" % ec.api_uri)
        l = len(json.loads(r.content))
        r.close()
        self.assertEqual(l, len(posts.ALL))
        now = time.time()
        nb = 100
        for i in xrange(nb):
            r = requests.get("%s/discovery" % ec.api_uri)
            r.close()
        self.assertTrue(now + (nb // 100) > time.time())
        r = requests.get("%s/discovery" % ec.api_uri)
        l = len(json.loads(r.content))
        r.close()
        self.assertEqual(l, len(posts.ALL))

    def test_08_backup(self):
        n = int(math.floor(time.time()))
        r = requests.post("%s/backup/db" % ec.api_uri)
        s = json.loads(r.content)
        r.close()
        self.assertTrue(s["copy"])
        self.assertTrue(os.path.isfile(s["dest_fs"]))
        os.remove(s["dest_fs"])
        self.assertTrue(n < s["ts"])

    def test_09(self):
        pass
