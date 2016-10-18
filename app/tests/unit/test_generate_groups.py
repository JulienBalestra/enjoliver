import os
import subprocess
from unittest import TestCase

import re

from app import generate_groups


class TestGenerateGroups(TestCase):
    gen = generate_groups.GenerateGroup
    network_environment = "%s/misc/network-environment" % gen.bootcfg_path
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.gen.project_path])
        cls.gen = generate_groups.GenerateGroup(
            _id="etcd-proxy", name="etcd-proxy", profile="TestGenerateProfiles")
        cls.gen.profiles_path = "%s/test_resources" % cls.tests_path
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    def test_00_ip_address(self):
        self.assertFalse(os.path.isfile("%s" % self.network_environment))
        ip = self.gen.ip_address
        match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
        self.assertIsNotNone(match)
        self.assertTrue(os.path.isfile("%s" % self.network_environment))

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': '', 'seed': 'http://%s:8080' % self.gen.ip_address}
        self.gen._metadata()
        self.assertEqual(expect, self.gen.target_data["metadata"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'etcd_initial_cluster': '',
                'seed': 'http://%s:8080' % self.gen.ip_address
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy'
        }
        new = generate_groups.GenerateGroup(
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml")
        result = new.generate()
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            bootcfg_path=self.test_bootcfg_path)
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_bootcfg_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_bootcfg_path, _id))
