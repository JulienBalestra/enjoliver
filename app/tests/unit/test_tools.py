import os
from unittest import TestCase

from app import tools


class TestTools(TestCase):
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]

    def test_00(self):
        self.assertIsNone(tools.get_verified_dns_query({
            u'mac': u'52:54:00:e8:32:5b',
            u'netmask': 21,
            u'ipv4': u'172.20.0.65',
            u'cidrv4': u'172.20.0.65/21',
            u'name': u'eth0',
            "gateway": "172.20.0.1",
            "fqdn": [
                "1.host.enjoliver.local"
            ]
        }))

    def test_01(self):
        self.assertEqual("localhost", tools.get_verified_dns_query({
            u'ipv4': u'127.0.0.1', u'cidrv4': u'127.0.0.1/21', u'name': u'eth0',
            "gateway": "127.0.0.1", "fqdn": ["localhost"]}))
