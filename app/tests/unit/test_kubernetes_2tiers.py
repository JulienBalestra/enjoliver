import os
from unittest import TestCase

from app.plans import kubernetes_2tiers


class TestKubernetes2tiers(TestCase):
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_matchbox_path = "%s/test_matchbox" % tests_path
    api_uri = "http://127.0.0.1:5000"

    @staticmethod
    def clean_sandbox():
        dirs = ["%s/%s" % (TestKubernetes2tiers.test_matchbox_path, k)
                for k in ("profiles", "groups")]
        for d in dirs:
            for f in os.listdir(d):
                if ".json" in f:
                    os.write(1, "\r-> remove %s/%s\n\r" % (d, f))
                    os.remove("%s/%s" % (d, f))

    def setUp(self):
        self.clean_sandbox()

    def test_00(self):
        kubernetes_2tiers.Kubernetes2Tiers(
            ignition_dict={"discovery": "unit-testkubernetes2tiers-discovery"},
            matchbox_path=self.test_matchbox_path,
            api_uri=self.api_uri,
            extra_selectors={}
        )
        kubernetes_2tiers.Kubernetes2Tiers(
            ignition_dict={"discovery": "unit-testkubernetes2tiers-discovery"},
            matchbox_path=self.test_matchbox_path,
            api_uri=self.api_uri,
            extra_selectors={}
        )
