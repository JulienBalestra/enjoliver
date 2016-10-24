import os
import subprocess
import unittest


class TestAssetsCoreOS(unittest.TestCase):
    func_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    assets_path = "%s/bootcfg/assets" % project_path
    asset_test = "%s/coreos" % assets_path
    default_files = ["Makefile"]

    def test_00_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_01_default(self):
        expect = self.default_files + ["1192.1.0"]
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_02_serve(self):
        expect = self.default_files + ["1192.1.0", "serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "serve"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_03_clean(self):
        expect = self.default_files + ["serve"]
        expect.sort()
        subprocess.check_output(["make", "-C", self.asset_test, "clean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_04_fclean(self):
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(self.default_files, real)


class TestAssetsSetupNetworkEnvironment(unittest.TestCase):
    func_path = "%s" % os.path.dirname(__file__)
    tests_path = os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    assets_path = "%s/bootcfg/assets" % project_path
    asset_test = "%s/setup-network-environment" % assets_path
    default_files = ["Makefile", "1.0.1-setup-network-environment.sha512"]

    def test_00_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_01_default(self):
        expect = self.default_files + ["1.0.1"]
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_02_serve(self):
        expect = self.default_files + ["1.0.1", "serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "serve"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_03_clean(self):
        expect = self.default_files + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "clean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_04_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)
