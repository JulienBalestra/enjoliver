import unittest

from app.monitoring import FlaskMonitoringComponents, CockroachDatabase, DatabaseMonitoringComponents


class TestFlaskMonitoringComponents(unittest.TestCase):
    def test_00(self):
        one = FlaskMonitoringComponents("one")
        oneone = FlaskMonitoringComponents("one")
        self.assertIs(one, oneone)
        two = FlaskMonitoringComponents("two")
        self.assertIsNot(one, two)

    def test_01(self):
        one = CockroachDatabase()
        two = CockroachDatabase()
        self.assertIs(one, two)

    def test_02(self):
        one = DatabaseMonitoringComponents("db")
        two = DatabaseMonitoringComponents("db")
        self.assertIs(one, two)
