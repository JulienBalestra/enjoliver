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
        expect = {
            u'flask': True,
            u'global': False,
            u'bootcfg': {
                u'/boot.ipxe': False,
                u'/boot.ipxe.0': False,
                u'/': False,
                u'/assets': False
            }}

        result = self.app.get('/healthz')
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.data)
        self.assertEqual(content, expect)

    def test_ipxe_boot(self):
        expect = '#!ipxe\n' \
                 'echo start /boot.ipxe\n' \
                 ':retry_dhcp\n' \
                 'dhcp || goto retry_dhcp\n' \
                 'chain http://localhost/ipxe?' \
                 'uuid=${uuid}&' \
                 'mac=${net0/mac:hexhyp}&' \
                 'domain=${domain}&' \
                 'hostname=${hostname}&' \
                 'serial=${serial}\n'

        result = self.app.get('/boot.ipxe')
        self.assertEqual(result.status_code, 200)
        content = result.data
        self.assertEqual(content, expect)

    def test_ipxe_boot_0(self):
        expect = '#!ipxe\n' \
                 'echo start /boot.ipxe\n' \
                 ':retry_dhcp\n' \
                 'dhcp || goto retry_dhcp\n' \
                 'chain http://localhost/ipxe?' \
                 'uuid=${uuid}&' \
                 'mac=${net0/mac:hexhyp}&' \
                 'domain=${domain}&' \
                 'hostname=${hostname}&' \
                 'serial=${serial}\n'

        result = self.app.get('/boot.ipxe')
        self.assertEqual(result.status_code, 200)
        content = result.data
        self.assertEqual(content, expect)

    def test_404(self):
        result = self.app.get('/fake')
        self.assertEqual(result.status_code, 404)
        content = result.data
        self.assertEqual(content, "404\n")

    def test_root(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.data)
        self.assertItemsEqual(content, [u'/boot.ipxe.0', u'/discovery', u'/boot.ipxe', u'/healthz', u'/ipxe', u'/'])
