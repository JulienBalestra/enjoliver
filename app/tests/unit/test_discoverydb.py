import copy
import unittest

from app import discoverydb

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


class TestDiscovery(unittest.TestCase):
    def test_00(self):
        d = discoverydb.Discovery(POST_ONE, None)
        self.assertEqual(d.mac, POST_ONE["boot-info"]["mac"])

    def test_01(self):
        del_interfaces = copy.deepcopy(POST_ONE)
        del del_interfaces["interfaces"][1]
        with self.assertRaises(LookupError):
            discoverydb.Discovery(del_interfaces, None)

    def test_02(self):
        d = discoverydb.Discovery(POST_ONE, None)
        self.assertEqual(d.refresh_cache(), [POST_ONE])

    def test_03(self):
        one = discoverydb.Discovery(POST_ONE, None)
        cache = one.refresh_cache()
        self.assertEqual(cache, [POST_ONE])
        two = discoverydb.Discovery(POST_ONE, cache)
        cache = two.refresh_cache()
        self.assertEqual(cache, [POST_ONE])

    def test_04(self):
        one = discoverydb.Discovery(POST_ONE, None)
        cache = one.refresh_cache()
        self.assertEqual(cache, [POST_ONE])
        two = discoverydb.Discovery(POST_TWO, cache)
        cache = two.refresh_cache()
        self.assertEqual(cache, [POST_ONE, POST_TWO])

    def test_05(self):
        one = discoverydb.Discovery(POST_ONE, None)
        cache = one.refresh_cache()
        self.assertEqual(cache, [POST_ONE])
        two = discoverydb.Discovery(POST_TWO, cache)
        cache = two.refresh_cache()
        self.assertEqual(cache, [POST_ONE, POST_TWO])

        one = discoverydb.Discovery(POST_ONE, cache)
        cache = one.refresh_cache()
        self.assertEqual(cache, [POST_ONE, POST_TWO])
        two = discoverydb.Discovery(POST_TWO, cache)
        cache = two.refresh_cache()
        self.assertEqual(cache, [POST_ONE, POST_TWO])

    def test_06(self):
        o = {
            u'boot-info':
                {
                    u'mac': u'52:54:00:90:c3:9',
                    u'uuid': u'ee378e7b-1575-425d-a6d6-e0dadb9f31a0'
                },
            u'lldp': {
                u'data': {
                    u'interfaces': [
                        {
                            u'chassis': {
                                u'id': u'28:f1:0e:12:20:00',
                                u'name': u'rkt-1d715f4e-575c-46ee-845e-31a021a95253'},
                            u'port': {u'id': u'fe:54:00:90:c3:9f'}
                        }
                    ]
                },
                u'is_file': True
            },
            u'interfaces': [
                {u'netmask': 8, u'MAC': u'', u'IPv4': u'127.0.0.1', u'CIDRv4': u'127.0.0.1/8', u'name': u'lo'},
                {u'netmask': 21, u'MAC': u'52:54:00:90:c3:9f', u'IPv4': u'172.20.0.81', u'CIDRv4': u'172.20.0.81/21',
                 u'name': u'eth0'}
            ]
        }
        one = discoverydb.Discovery(o, None)
        cache = one.refresh_cache()
        self.assertEqual(cache, [o])
