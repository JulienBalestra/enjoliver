#! /usr/bin/env python3
import os
import unittest


class TestValidateMatchboxAssets(unittest.TestCase):
    cwd = os.path.dirname(os.path.abspath(__file__))
    matchbox = os.getenv("CHECK_MATCHBOX_PATH", "%s/matchbox" % cwd)
    assets = "%s/assets" % matchbox

    def test_discoveryC(self):
        rule = "%s/%s/serve" % (self.assets, self.test_discoveryC.__name__.replace("test_", ""))
        list_dir = os.listdir(rule)
        self.assertIn("discoveryC", list_dir)


if __name__ == '__main__':
    unittest.main()
