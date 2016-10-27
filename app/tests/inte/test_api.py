import httplib
import json
import os
import subprocess
import urllib2
from multiprocessing import Process

import sys

import time

from app import api
import unittest


class TestAPI(unittest.TestCase):
    p_bootcfg = Process

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
    def process_target():
        cmd = [
            "%s/bootcfg_dir/bootcfg" % TestAPI.tests_path,
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
        cls.app = api.app.test_client()
        cls.app.testing = True

        subprocess.check_output(["make"], cwd=cls.project_path)
        if os.path.isfile("%s/bootcfg_dir/bootcfg" % TestAPI.tests_path) is False:
            subprocess.check_output(["make"], cwd=cls.tests_path)
        cls.p_bootcfg = Process(target=TestAPI.process_target)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_bootcfg.start()
        assert cls.p_bootcfg.is_alive() is True

        cls.bootcfg_running(cls.bootcfg_endpoint, cls.p_bootcfg)

    @classmethod
    def tearDownClass(cls):
        os.write(1, "TERM -> %d\n" % cls.p_bootcfg.pid)
        sys.stdout.flush()
        cls.p_bootcfg.terminate()
        cls.p_bootcfg.join(timeout=5)
        # cls.clean_sandbox()

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

    def test_healthz_00(self):
        result = self.app.get('/healthz')
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.data)
        self.assertEqual(content, {
            u'bootcfg': {u'boot.ipxe': True},
            u'flask': True,
            u'global': True})
