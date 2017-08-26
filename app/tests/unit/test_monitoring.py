import unittest

from app.monitoring import FlaskMonitoringComponents


class TestFlaskMonitoringComponents(unittest.TestCase):
    def test_00(self):
        one = FlaskMonitoringComponents("/one")
        oneone = FlaskMonitoringComponents("/one")
        self.assertIs(one, oneone)
        two = FlaskMonitoringComponents("/two")
        self.assertIsNot(one, two)

    def test_01(self):
        one = FlaskMonitoringComponents("/one")
        self.assertEqual("one", one.route_name)

    def test_02(self):
        two = FlaskMonitoringComponents("/two/toto")
        self.assertEqual("two_toto", two.route_name)

    def test_03(self):
        three = FlaskMonitoringComponents("/three/toto/<path:path>")
        self.assertEqual("three_toto", three.route_name)

    def test_04(self):
        four = FlaskMonitoringComponents("/four/toto/<path:path>/titi")
        self.assertEqual("four_toto", four.route_name)
