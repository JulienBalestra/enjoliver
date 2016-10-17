from unittest import TestCase

import re

from app import generate_profiles


class TestGenerateProfiles(TestCase):
    gen = generate_profiles.GenerateProfiles

    @classmethod
    def setUpClass(cls):
        cls.gen = generate_profiles.GenerateProfiles()

    def test_00_ip_address(self):
        ip = self.gen.ip_address
        match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
        self.assertIsNotNone(match)
