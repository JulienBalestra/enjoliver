import unittest

from app.monitoring import DatabaseMonitoring


class TestMonitoring(unittest.TestCase):
    @unittest.skip("")
    def test_01(self):
        one = DatabaseMonitoring()
        two = DatabaseMonitoring()
        self.assertIs(one, two)
