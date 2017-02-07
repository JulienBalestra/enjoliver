import os
from unittest import TestCase

from app import generate_profiles, generate_common


class IOErrorToWarning(object):
    def __enter__(self):
        generate_common.GenerateCommon._raise_enof = Warning

    def __exit__(self, ext, exv, trb):
        generate_common.GenerateCommon._raise_enof = IOError


class TestGenerateProfiles(TestCase):
    gen = generate_profiles.GenerateProfile
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path
    api_uri = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        generate_common.GenerateCommon._raise_enof = Warning  # Skip the ignition isfile
        with IOErrorToWarning():
            cls.gen = generate_profiles.GenerateProfile(
                api_uri=cls.api_uri,
                _id="etcd-proxy",
                name="etcd-proxy",
                ignition_id="etcd-proxy.yaml",
                bootcfg_path=cls.test_bootcfg_path
            )
        generate_common.GenerateCommon._raise_enof = IOError
        cls.gen.profiles_path = "%s/test_resources" % cls.tests_path

    def test_01_boot(self):
        expect = {
            'kernel': '%s/assets/coreos/serve/coreos_production_pxe.vmlinuz' % self.gen.api_uri,
            'initrd': ['%s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz' % self.gen.api_uri],
            'cmdline':
                {
                    'coreos.autologin': '',
                    'coreos.first_boot': '',
                    'coreos.oem.id': 'pxe',
                    'coreos.config.url': '%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}' % self.gen.api_uri
                }
        }
        self.gen._boot()

        self.assertEqual(expect, self.gen._target_data["boot"])

    def test_990_generate(self):
        expect = {
            "cloud_id": "",
            "boot": {
                "kernel": "%s/assets/coreos/serve/coreos_production_pxe.vmlinuz" % self.gen.api_uri,
                "initrd": [
                    "%s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz" % self.gen.api_uri
                ],
                "cmdline": {
                    "coreos.autologin": "",
                    "coreos.first_boot": "",
                    "coreos.oem.id": "pxe",
                    "coreos.config.url": "%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}" %
                                         self.gen.api_uri
                }
            },
            "id": "etcd-proxy",
            "ignition_id": "etcd-proxy.yaml",
            "name": "etcd-proxy"
        }
        with IOErrorToWarning():
            new = generate_profiles.GenerateProfile(
                api_uri=self.api_uri,
                _id="etcd-proxy",
                name="etcd-proxy",
                ignition_id="etcd-proxy.yaml",
                bootcfg_path=self.test_bootcfg_path
            )
        result = new.generate()
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        with IOErrorToWarning():
            new = generate_profiles.GenerateProfile(
                api_uri=self.api_uri,
                _id="%s" % _id,
                name="etcd-test",
                ignition_id="etcd-test.yaml",
                bootcfg_path=self.test_bootcfg_path
            )
        new.dump()
        self.assertTrue(os.path.isfile("%s/profiles/%s.json" % (self.test_bootcfg_path, _id)))
        os.remove("%s/profiles/%s.json" % (self.test_bootcfg_path, _id))
