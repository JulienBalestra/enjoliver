import os
import subprocess
from unittest import TestCase

import re

from app import generate_profiles


class TestGenerateProfiles(TestCase):
    gen = generate_profiles.GenerateProfiles
    network_environment = "%s/misc/network-environment" % gen.bootcfg_path

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.gen.project_path])
        cls.gen = generate_profiles.GenerateProfiles()
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    def test_00_ip_address(self):
        self.assertFalse(os.path.isfile("%s" % self.network_environment))
        ip = self.gen.ip_address
        match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
        self.assertIsNotNone(match)
        self.assertTrue(os.path.isfile("%s" % self.network_environment))
