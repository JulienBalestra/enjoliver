import httplib
import os
import urllib2
from unittest import TestCase
from multiprocessing import Process
import subprocess

import time


class TestBootCFG(TestCase):
    p_bootcfg = Process

    tests_path = "%s" % os.path.dirname(__file__)
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path
    assets_path = "%s/bootcfg/assets" % project_path

    bootcfg_address = "127.0.0.1:8080"
    bootcfg_endpoint = "http://%s" % bootcfg_address

    @staticmethod
    def run_bootcfg():
        cmd = [
            "%s/bin/bootcfg" % TestBootCFG.tests_path,
            "-data-path", "%s" % TestBootCFG.bootcfg_path,
            "-assets-path", "%s" % TestBootCFG.assets_path,
            "-address", "%s" % TestBootCFG.bootcfg_address
        ]
        print " ".join(cmd)
        os.execv(cmd[0], cmd)

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make"], cwd=cls.tests_path)
        cls.p_bootcfg = Process(target=TestBootCFG.run_bootcfg)
        cls.p_bootcfg.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        print "\nSIGTERM -> %d" % cls.p_bootcfg.pid

        cls.p_bootcfg.terminate()
        cls.p_bootcfg.join(timeout=5)

    def setUp(self):
        self.assertTrue(self.p_bootcfg.is_alive())

    def test_00_bootcfg_running(self):
        response = ""
        for i in xrange(10):
            try:
                response = urllib2.urlopen(self.bootcfg_endpoint).read()
                break
            except httplib.BadStatusLine:
                time.sleep(0.1)
        self.assertEqual("bootcfg\n", response)

    def test_01_bootcfg_ipxe(self):
        response = urllib2.urlopen("%s/ipxe" % self.bootcfg_endpoint).read()
        response = response.split("\n")
        self.assertIn("#!ipxe", response[0])
