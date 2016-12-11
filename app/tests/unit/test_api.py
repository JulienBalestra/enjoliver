import json
import os
import unittest

from app import api
from app import model
from common import posts


class TestAPI(unittest.TestCase):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path

    @classmethod
    def setUpClass(cls):
        db_path = "%s/%s.sqlite" % (cls.dbs_path, TestAPI.__name__.lower())
        db = "sqlite:///%s" % db_path
        try:
            os.remove(db_path)
        except OSError:
            pass
        engine = api.create_engine(db)
        model.Base.metadata.create_all(engine)
        api.engine = engine
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

        result = self.app.get('/boot.ipxe.0')
        self.assertEqual(result.status_code, 200)
        content = result.data
        self.assertEqual(content, expect)

    def test_ipxe(self):
        result = self.app.get('/ipxe?uuid=fake?mac=fake')
        self.assertEqual(result.status_code, 404)

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
            u'/discovery/ignition-journal/<string:uuid>',
            u'/boot.ipxe',
            u'/healthz',
            u'/ipxe',
            u'/'])

    def test_discovery_00(self):
        result = self.app.post('/discovery', data=json.dumps(posts.M01),
                               content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {u'total_elt': 1, u'new': True})
        result = self.app.post('/discovery', data=json.dumps(posts.M02),
                               content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {u'total_elt': 2, u'new': True})

    def test_discovery_01(self):
        discovery_data = "bad"
        result = self.app.post('/discovery', data=json.dumps(discovery_data),
                               content_type='application/json')
        self.assertEqual(result.status_code, 406)
        self.assertEqual(json.loads(result.data), {u'boot-info': {}, u'interfaces': [], u'lldp': {}})

    def test_discovery_02(self):
        for i in xrange(5):
            r = self.app.get("/discovery")
            self.assertEqual(200, r.status_code)
            data = json.loads(r.data)
            self.assertEqual(2, len(data))

    def test_discovery_03(self):
        r = self.app.get("/discovery/interfaces")
        self.assertEqual(200, r.status_code)
        data = json.loads(r.data)
        self.assertEqual(2, len(data))

    def test_discovery_04(self):
        uuid = posts.M01["boot-info"]["uuid"]
        r = self.app.get("/discovery/ignition-journal/%s" % uuid)
        self.assertEqual(200, r.status_code)
        data = json.loads(r.data)
        self.assertEqual(39, len(data))

    def test_discovery_05(self):
        r = self.app.get("/discovery")

        for m in json.loads(r.data):
            uuid = m["boot-info"]["uuid"]
            r = self.app.get("/discovery/ignition-journal/%s" % uuid)
            self.assertEqual(200, r.status_code)
