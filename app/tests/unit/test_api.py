import json

from app import api
import unittest



POST_ONE = {
    u'boot-info': {
        u'mac': u'52:54:00:ea:93:b7',
        u'uuid': u'769ea7b-6192-433d-a775-b215d5fbd64f'},
    u'lldp': {
        u'data': {
            u'interfaces': [
                {
                    u'chassis': {
                        u'id': u'28:f1:0e:12:20:00',
                        u'name': u'E7470'},
                    u'port': {
                        u'id': u'fe:54:00:ea:93:b7'}
                }
            ]
        },
        u'is_file': True},
    u'interfaces': [
        {
            u'netmask': 8,
            u'MAC': u'',
            u'IPv4': u'127.0.0.1',
            u'CIDRv4': u'127.0.0.1/8',
            u'name': u'lo'},
        {
            u'netmask': 21,
            u'MAC': u'52:54:00:ea:93:b7',
            u'IPv4': u'172.20.0.65',
            u'CIDRv4': u'172.20.0.65/21',
            u'name': u'eth0'
        }
    ]
}

POST_TWO = {
    u'boot-info': {
        u'mac': u'52:54:00:ea:93:02',
        u'uuid': u'769ea7b-6192-433d-a775-b215d5fbd64f'},
    u'lldp': {
        u'data': {
            u'interfaces': [
                {
                    u'chassis': {
                        u'id': u'28:f1:0e:12:20:00',
                        u'name': u'E7470'},
                    u'port': {
                        u'id': u'fe:54:00:ea:93:02'}
                }
            ]
        },
        u'is_file': True},
    u'interfaces': [
        {
            u'netmask': 8,
            u'MAC': u'',
            u'IPv4': u'127.0.0.1',
            u'CIDRv4': u'127.0.0.1/8',
            u'name': u'lo'},
        {
            u'netmask': 21,
            u'MAC': u'52:54:00:ea:93:02',
            u'IPv4': u'172.20.0.66',
            u'CIDRv4': u'172.20.0.66/21',
            u'name': u'eth0'
        }
    ]
}


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
        self.assertItemsEqual(content, [
            u'/boot.ipxe.0',
            u'/discovery',
            u'/discovery/interfaces',
            u'/boot.ipxe',
            u'/healthz',
            u'/ipxe',
            u'/'])

    def test_discovery_00(self):
        discovery_data = {
            "interfaces": [
                {"IPv4": "192.168.1.1",
                 "CIDRv4": "192.168.1.1/24",
                 "netmask": 24,
                 "MAC": "00:00:00:00:00",
                 "name": "eth0"}]}
        result = self.app.post('/discovery', data=json.dumps(POST_ONE),
                               content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {u'total_elt': 1, u'update': False})
        result = self.app.post('/discovery', data=json.dumps(POST_TWO),
                               content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {u'total_elt': 2, u'update': False})

    def test_discovery_01(self):
        discovery_data = "bad"
        result = self.app.post('/discovery', data=json.dumps(discovery_data),
                               content_type='application/json')
        self.assertEqual(result.status_code, 400)
        self.assertEqual(json.loads(result.data), {u'boot-info': {}, u'interfaces': [], u'lldp': {}})
