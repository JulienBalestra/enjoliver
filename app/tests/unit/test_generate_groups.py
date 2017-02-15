import os
from unittest import TestCase

from app import generate_groups


class TestGenerateGroups(TestCase):
    gen = generate_groups.GenerateGroup
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_matchbox_path = "%s/test_matchbox" % tests_path
    api_uri = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        cls.gen = generate_groups.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            matchbox_path=cls.test_matchbox_path
        )
        cls.gen.profiles_path = "%s/test_resources" % cls.tests_path

    def test_00_uri(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': '',
                  'api_uri': '%s' % self.gen.api_uri,
                  'ssh_authorized_keys': []}

        self.gen._metadata()
        self.assertEqual(expect['api_uri'], self.gen._target_data["metadata"]["api_uri"])
        self.assertEqual(expect['etcd_initial_cluster'], self.gen._target_data["metadata"]["etcd_initial_cluster"])

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
            api_uri=self.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="etcd-proxy.yaml",
            matchbox_path=self.test_matchbox_path
        )
        result = new.generate()
        self.assertEqual(expect["profile"], result["profile"])
        self.assertEqual(expect["id"], result["id"])
        self.assertEqual(expect["name"], result["name"])
        self.assertEqual(expect["metadata"]["api_uri"], result["metadata"]["api_uri"])

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            api_uri=self.api_uri,
            _id=_id,
            name="etcd-test",
            profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path
        )
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))


class TestGenerateGroupsSelectorLower(TestCase):
    gen = generate_groups.GenerateGroup
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_matchbox_path = "%s/test_matchbox" % tests_path
    api_uri = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        cls.gen = generate_groups.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=cls.test_matchbox_path
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def test_00_api_uri(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {
            'etcd_initial_cluster': '',
            'api_uri': "%s" % self.gen.api_uri,
            'ssh_authorized_keys': []
        }
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
            api_uri=self.api_uri,
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=self.test_matchbox_path)
        result = new.generate()
        result["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            api_uri=self.api_uri,
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path,
            selector={"mac": "08:00:27:37:28:2e"}
        )
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))


class TestGenerateGroupsSelectorUpper(TestCase):
    gen = generate_groups.GenerateGroup
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_matchbox_path = "%s/test_matchbox" % tests_path
    api_uri = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        cls.gen = generate_groups.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2E"},
            matchbox_path=cls.test_matchbox_path
        )

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
            api_uri=self.api_uri, _id="etcd-proxy",
            name="etcd-proxy",
            profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=self.test_matchbox_path
        )
        result = new.generate()
        result["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            api_uri=self.api_uri,
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path,
            selector={"mac": "08:00:27:37:28:2e"}
        )
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))


class TestGenerateGroupsExtraMetadata(TestCase):
    gen = generate_groups.GenerateGroup
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_matchbox_path = "%s/test_matchbox" % tests_path
    api_uri = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        cls.gen = generate_groups.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2E"},
            metadata={"etcd_initial_cluster": "static0=http://192.168.1.1:2379",
                      "api_seed": "http://192.168.1.2:5000"},
            matchbox_path=cls.test_matchbox_path
        )

    def test_00_api_uri(self):
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
            api_uri=self.api_uri,
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=self.test_matchbox_path
        )
        result = new.generate()
        result["metadata"]["ssh_authorized_keys"] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generate_groups.GenerateGroup(
            api_uri=self.api_uri,
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path,
            selector={"mac": "08:00:27:37:28:2e"}
        )
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))
