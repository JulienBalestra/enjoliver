import json

from app import api
import unittest


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = api.app.test_client()
        cls.app.testing = True

    @classmethod
    def tearDownClass(cls):
        pass

    def test_healthz_00(self):
        result = self.app.get('/healthz')
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.data)
        self.assertEqual(content, {u'bootcfg': {u'boot.ipxe': False}, u'flask': True, u'global': False})
