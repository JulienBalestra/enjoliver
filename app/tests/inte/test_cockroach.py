"""
Manual test suite for CockroachDB integration

rkt run --net=host --insecure-options=all --interactive aci-cockroachdb --exec /usr/local/bin/cockroach -- start

rkt run --net=host --insecure-options=all --interactive aci-cockroachdb --exec /usr/local/bin/cockroach -- start \
    --port 26258 --join=localhost:26257 --http-port 8081

rkt run --net=host --insecure-options=all --interactive aci-cockroachdb --exec /usr/local/bin/cockroach -- start \
    --port 26259 --join=localhost:26257 --http-port 8082
"""
import os
import time
import unittest
from multiprocessing import Process

import requests

from app import configs
from app import smartdb

EC = configs.EnjoliverConfig(importer=__file__)
EC.api_uri = "http://127.0.0.1:5000"
EC.db_uri = "cockroachdb://root@localhost:26257,cockroachdb://root@localhost:26258,cockroachdb://root@localhost:26259"


@unittest.skip("Manual Trigger -> TODO")
class TestEnjoliverCockroach(unittest.TestCase):
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

    @classmethod
    def setUpClass(cls):
        cls.smart = smartdb.SmartClient(EC.db_uri)
        cls.p_matchbox = Process(target=TestEnjoliverCockroach.process_target_matchbox)
        cls.p_api = Process(target=TestEnjoliverCockroach.process_target_api)

        print("PPID -> %s\n" % os.getpid())
        cls.p_matchbox.start()
        assert cls.p_matchbox.is_alive() is True
        cls.p_api.start()
        assert cls.p_api.is_alive() is True

        cls.api_running(EC.api_uri, cls.p_api)
        cls.smart.create_base()

    @classmethod
    def tearDownClass(cls):
        cls.p_matchbox.terminate()
        cls.p_matchbox.join(timeout=5)
        cls.p_api.terminate()
        cls.p_api.join(timeout=5)
        time.sleep(0.2)

    @staticmethod
    def api_running(api_endpoint, p_api):
        response_code = 404
        for i in range(10):
            assert p_api.is_alive() is True
            try:
                request = requests.get(api_endpoint)
                response_code = request.status_code
                request.close()
                break

            except requests.exceptions.ConnectionError:
                pass
            time.sleep(0.2)

        assert 200 == response_code

    @staticmethod
    def process_target_matchbox():
        os.environ["ENJOLIVER_MATCHBOX_PATH"] = TestEnjoliverCockroach.test_matchbox_path
        os.environ["ENJOLIVER_MATCHBOX_ASSETS"] = TestEnjoliverCockroach.assets_path

        cmd = [
            "%s/manage.py" % TestEnjoliverCockroach.project_path,
            "matchbox"
        ]
        print("PID  -> %s\n"
              "exec -> %s\n" % (
                  os.getpid(), " ".join(cmd)))
        os.execve(cmd[0], cmd, os.environ)

    @staticmethod
    def process_target_api():
        os.environ["ENJOLIVER_DB_URI"] = EC.db_uri
        os.environ["ENJOLIVER_API_URI"] = EC.api_uri
        os.environ["ENJOLIVER_GUNICORN_WORKERS"] = "3"
        os.environ["ENJOLIVER_LOGGING_LEVEL"] = "INFO"
        cmd = [
            "%s/manage.py" % TestEnjoliverCockroach.project_path,
            "gunicorn"
        ]
        os.execve(cmd[0], cmd, os.environ)

    def test_00(self):
        for i in range(100):
            requests.get("%s/healthz" % EC.api_uri)
