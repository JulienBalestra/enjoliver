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

    bootcfg_port = os.getenv("BOOTCFG_PORT", "8080")

    @classmethod
    def setUpClass(cls):
        os.environ["API_URI"] = "http://127.0.0.1:5000"
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

    def test_00_uri(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': '',
                  'api_uri': '%s' % self.gen.api_uri,
                  'ssh_authorized_keys': []}

        self.gen._metadata()
        self.assertEqual(expect, self.gen._target_data["metadata"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'etcd_initial_cluster': '',
                'api_uri': '%s' % self.gen.api_uri,
                'ssh_authorized_keys': []
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


class TestGenerateGroupsSelectorLower(TestCase):
    gen = generate_groups.GenerateGroup
    network_environment = "%s/misc/network-environment" % gen.bootcfg_path
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    bootcfg_port = os.getenv("BOOTCFG_PORT", "8080")

    @classmethod
    def setUpClass(cls):
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        subprocess.check_output(["make", "-C", cls.gen.project_path])
        cls.gen = generate_groups.GenerateGroup(
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2e"},
            bootcfg_path=cls.test_bootcfg_path)
        # cls.gen.profiles_path = "%s/test_resources" % cls.tests_path
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    def test_00_api_uri(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': '',
                  'api_uri': "%s" % self.gen.api_uri,
                  'ssh_authorized_keys': []}
        self.gen._metadata()
        self.gen._target_data["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, self.gen._target_data["metadata"])

    def test_02_selector(self):
        expect = {'mac': '08:00:27:37:28:2e'}
        self.gen._selector()
        self.assertEqual(expect, self.gen._target_data["selector"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'etcd_initial_cluster': '',
                'api_uri': self.gen.api_uri,
                'selector': {'mac': '08:00:27:37:28:2e'},
                'ssh_authorized_keys': []
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy',
            'selector': {'mac': '08:00:27:37:28:2e'}
        }
        new = generate_groups.GenerateGroup(
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            bootcfg_path=self.test_bootcfg_path)
        result = new.generate()
        result["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            bootcfg_path=self.test_bootcfg_path,
            selector={"mac": "08:00:27:37:28:2e"})
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_bootcfg_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_bootcfg_path, _id))


class TestGenerateGroupsSelectorUpper(TestCase):
    gen = generate_groups.GenerateGroup
    network_environment = "%s/misc/network-environment" % gen.bootcfg_path
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    bootcfg_port = os.getenv("BOOTCFG_PORT", "8080")

    @classmethod
    def setUpClass(cls):
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        subprocess.check_output(["make", "-C", cls.gen.project_path])
        cls.gen = generate_groups.GenerateGroup(
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2E"},
            bootcfg_path=cls.test_bootcfg_path)
        # cls.gen.profiles_path = "%s/test_resources" % cls.tests_path
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    def test_00_ip_address(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': '',
                  'api_uri': "%s" % self.gen.api_uri,
                  'ssh_authorized_keys': []}
        self.gen._metadata()
        self.gen._target_data["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, self.gen._target_data["metadata"])

    def test_02_selector(self):
        expect = {'mac': '08:00:27:37:28:2e'}
        self.gen._selector()
        self.assertEqual(expect, self.gen._target_data["selector"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'etcd_initial_cluster': '',
                'api_uri': "%s" % self.gen.api_uri,
                'selector': {'mac': '08:00:27:37:28:2e'},
                'ssh_authorized_keys': []
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy',
            'selector': {'mac': '08:00:27:37:28:2e'}
        }
        new = generate_groups.GenerateGroup(
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            bootcfg_path=self.test_bootcfg_path)
        result = new.generate()
        result["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            bootcfg_path=self.test_bootcfg_path,
            selector={"mac": "08:00:27:37:28:2e"})
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_bootcfg_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_bootcfg_path, _id))


class TestGenerateGroupsExtraMetadata(TestCase):
    gen = generate_groups.GenerateGroup
    network_environment = "%s/misc/network-environment" % gen.bootcfg_path
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    bootcfg_port = os.getenv("BOOTCFG_PORT", "8080")

    @classmethod
    def setUpClass(cls):
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        subprocess.check_output(["make", "-C", cls.gen.project_path])
        cls.gen = generate_groups.GenerateGroup(
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2E"},
            metadata={"etcd_initial_cluster": "static0=http://192.168.1.1:2379",
                      "api_seed": "http://192.168.1.2:5000"},
            bootcfg_path=cls.test_bootcfg_path)
        # cls.gen.profiles_path = "%s/test_resources" % cls.tests_path
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    def test_00_api_uri(self):
        self.assertFalse(os.path.isfile("%s" % self.network_environment))
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': 'static0=http://192.168.1.1:2379',
                  'api_uri': "%s" % self.gen.api_uri,
                  'api_seed': 'http://192.168.1.2:5000',
                  'ssh_authorized_keys': []}
        self.gen._metadata()
        self.gen._target_data["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, self.gen._target_data["metadata"])

    def test_02_selector(self):
        expect = {'mac': '08:00:27:37:28:2e'}
        self.gen._selector()
        self.assertEqual(expect, self.gen._target_data["selector"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'etcd_initial_cluster': '',
                'api_uri': "%s" % self.gen.api_uri,
                'selector': {'mac': '08:00:27:37:28:2e'},
                'ssh_authorized_keys': []
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy',
            'selector': {'mac': '08:00:27:37:28:2e'}
        }
        new = generate_groups.GenerateGroup(
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            bootcfg_path=self.test_bootcfg_path)
        result = new.generate()
        result["metadata"]["ssh_authorized_keys"] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            bootcfg_path=self.test_bootcfg_path,
            selector={"mac": "08:00:27:37:28:2e"})
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_bootcfg_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_bootcfg_path, _id))
