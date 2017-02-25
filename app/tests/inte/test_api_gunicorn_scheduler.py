import httplib
import json
import os
import shutil
import sys
import time
import unittest
import urllib2
from multiprocessing import Process

import requests

from app import api
from app import configs
from app import model
from app import schedulerv2
from app import sync_matchbox
from common import posts

ec = configs.EnjoliverConfig(importer=__file__)
ec.api_uri = "http://127.0.0.1:5000"


class TestAPIGunicornScheduler(unittest.TestCase):
    p_matchbox = Process
    p_api = Process

    inte_path = "%s" % os.path.dirname(__file__)
    dbs_path = "%s/dbs" % inte_path
    tests_path = "%s" % os.path.dirname(inte_path)
    app_path = os.path.dirname(tests_path)
    project_path = os.path.dirname(app_path)
    matchbox_path = "%s/matchbox" % project_path
    assets_path = "%s/matchbox/assets" % project_path

    test_matchbox_path = "%s/test_matchbox" % tests_path

    api_discovery = "%s/discovery" % ec.api_uri

    @staticmethod
    def process_target_matchbox():
        os.environ["ENJOLIVER_MATCHBOX_PATH"] = TestAPIGunicornScheduler.test_matchbox_path
        os.environ["ENJOLIVER_MATCHBOX_ASSETS"] = TestAPIGunicornScheduler.assets_path
        cmd = [
            "%s/manage.py" % TestAPIGunicornScheduler.project_path,
            "matchbox"
        ]
        os.write(1, "PID  -> %s\n"
                    "exec -> %s\n" % (
                     os.getpid(), " ".join(cmd)))
        sys.stdout.flush()
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestAPIGunicornScheduler.test_matchbox_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s\n\r" % f)
                    os.remove("%s/%s" % (d, f))

    @staticmethod
    def process_target_api():
        cmd = [
            "%s/manage.py" % TestAPIGunicornScheduler.project_path,
            "gunicorn"
        ]
        os.execve(cmd[0], cmd, os.environ)

    @classmethod
    def setUpClass(cls):
        time.sleep(0.1)
        try:
            os.remove(ec.db_path)
        except OSError:
            pass

        shutil.rmtree(ec.ignition_journal_dir, ignore_errors=True)

        cls.clean_sandbox()

        engine = api.create_engine(ec.db_uri)
        model.Base.metadata.create_all(engine)
        api.engine = engine

        cls.p_matchbox = Process(target=TestAPIGunicornScheduler.process_target_matchbox)
        cls.p_api = Process(target=TestAPIGunicornScheduler.process_target_api)
        os.write(1, "PPID -> %s\n" % os.getpid())
        cls.p_matchbox.start()
        assert cls.p_matchbox.is_alive() is True
        cls.p_api.start()
        assert cls.p_api.is_alive() is True

        cls.matchbox_running(ec.matchbox_uri, cls.p_matchbox)
        cls.api_running(ec.api_uri, cls.p_api)

    @classmethod
    def tearDownClass(cls):
        os.write(1, "TERM -> %d\n" % cls.p_matchbox.pid)
        sys.stdout.flush()
        cls.p_matchbox.terminate()
        cls.p_matchbox.join(timeout=5)
        cls.p_api.terminate()
        cls.p_api.join(timeout=5)
        time.sleep(0.2)

    @staticmethod
    def matchbox_running(matchbox_endpoint, p_matchbox):
        response_body = ""
        response_code = 404
        for i in xrange(10):
            assert p_matchbox.is_alive() is True
            try:
                request = urllib2.urlopen(matchbox_endpoint)
                response_body = request.read()
                response_code = request.code
                request.close()
                break

            except (httplib.BadStatusLine, urllib2.URLError):
                pass
            time.sleep(0.2)

        assert "matchbox\n" == response_body
        assert 200 == response_code

    @staticmethod
    def api_running(api_endpoint, p_api):
        response_code = 404
        for i in xrange(10):
            assert p_api.is_alive() is True
            try:
                request = urllib2.urlopen(api_endpoint)
                response_code = request.code
                request.close()
                break

            except (httplib.BadStatusLine, urllib2.URLError):
                pass
            time.sleep(0.2)

        assert 200 == response_code

    def setUp(self):
        self.assertTrue(self.p_matchbox.is_alive())
        self.assertTrue(self.p_api.is_alive())
        self.api_healthz()

    def api_healthz(self):
        expect = {
            u'flask': True,
            u'global': True,
            u'db': True,
            u'matchbox': {
                u'/': True,
                u'/boot.ipxe': True,
                u'/boot.ipxe.0': True,
                u'/assets': True,
                u"/metadata": True
            }}
        request = urllib2.urlopen("%s/healthz" % ec.api_uri)
        response_body = request.read()
        response_code = request.code
        request.close()
        self.assertEqual(json.loads(response_body), expect)
        self.assertEqual(200, response_code)


# @unittest.skip("skip")
class TestEtcdMemberKubernetesControlPlane1(TestAPIGunicornScheduler):
    def test_01(self):
        r = requests.post(self.api_discovery, data=json.dumps(posts.M01))
        self.assertEqual(r.status_code, 200)
        sch = schedulerv2.EtcdMemberKubernetesControlPlane(ec.api_uri)
        sch.expected_nb = 1
        self.assertTrue(sch.apply())
        self.assertTrue(sch.apply())


class TestEtcdMemberKubernetesControlPlane2(TestAPIGunicornScheduler):
    def test_02(self):
        r = requests.post(self.api_discovery, data=json.dumps(posts.M01))
        r.close()
        self.assertEqual(r.status_code, 200)
        sch = schedulerv2.EtcdMemberKubernetesControlPlane(ec.api_uri)
        self.assertFalse(sch.apply())
        self.assertFalse(sch.apply())
        r = requests.post(self.api_discovery, data=json.dumps(posts.M02))
        r.close()
        self.assertFalse(sch.apply())
        r = requests.post(self.api_discovery, data=json.dumps(posts.M03))
        r.close()
        self.assertTrue(sch.apply())

        s = sync_matchbox.ConfigSyncSchedules(
            ec.api_uri,
            self.test_matchbox_path,
            ignition_dict={
                "etcd_member_kubernetes_control_plane": "inte-testapigunicornscheduler-etcd-k8s-cp",
                "kubernetes_nodes": "inte-testapigunicornscheduler-etcd-k8s-cp",
            }
        )
        s.apply()


class TestEtcdMemberKubernetesControlPlane3(TestAPIGunicornScheduler):
    def test_03(self):
        r = requests.post(self.api_discovery, data=json.dumps(posts.M01))
        r.close()
        self.assertEqual(r.status_code, 200)
        sch = schedulerv2.EtcdMemberKubernetesControlPlane(ec.api_uri)
        self.assertFalse(sch.apply())
        self.assertFalse(sch.apply())
        r = requests.post(self.api_discovery, data=json.dumps(posts.M02))
        r.close()
        self.assertFalse(sch.apply())
        r = requests.post(self.api_discovery, data=json.dumps(posts.M03))
        r.close()
        self.assertTrue(sch.apply())

        sch_no = schedulerv2.KubernetesNode(ec.api_uri, True)
        self.assertEqual(0, sch_no.apply())
        r = requests.post(self.api_discovery, data=json.dumps(posts.M04))
        r.close()
        self.assertEqual(1, sch_no.apply())

        s = sync_matchbox.ConfigSyncSchedules(
            ec.api_uri,
            self.test_matchbox_path,
            ignition_dict={
                "etcd_member_kubernetes_control_plane": "inte-testapigunicornscheduler-etcd-k8s-cp",
                "kubernetes_nodes": "inte-testapigunicornscheduler-etcd-k8s-cp",
            },
        )
        s.apply()


class TestEtcdMemberKubernetesControlPlane4(TestAPIGunicornScheduler):
    def test_04(self):
        for p in posts.ALL:
            r = requests.post(self.api_discovery, data=json.dumps(p))
            self.assertEqual(r.status_code, 200)
            r.close()

        sch_no = schedulerv2.KubernetesNode(ec.api_uri, True)

        self.assertEqual(len(posts.ALL) - schedulerv2.EtcdMemberKubernetesControlPlane.expected_nb, sch_no.apply())

        s = sync_matchbox.ConfigSyncSchedules(
            ec.api_uri,
            self.test_matchbox_path,
            ignition_dict={
                "etcd_member_kubernetes_control_plane": "inte-testapigunicornscheduler-etcd-k8s-cp",
                "kubernetes_nodes": "inte-testapigunicornscheduler-etcd-k8s-cp",
            },
            extra_selector_dict={"os": "installed"},
        )
        s.apply()
