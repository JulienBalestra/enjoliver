import unittest

from app.monitoring import FlaskMonitoringComponents


class TestFlaskMonitoringComponents(unittest.TestCase):
    def test_00(self):
        one = FlaskMonitoringComponents("one")
        oneone = FlaskMonitoringComponents("one")
        self.assertIs(one, oneone)
        two = FlaskMonitoringComponents("two")
        self.assertIsNot(one, two)

