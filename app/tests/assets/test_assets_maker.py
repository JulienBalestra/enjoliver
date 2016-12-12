import os
import subprocess
import unittest


@unittest.skipIf(os.getenv("PYCHARM_HOSTED"), "PYCHARM_HOSTED")
@unittest.skipIf(os.getenv("SKIP_ASSETS"), "SKIP_ASSETS")
class TestAssetsCoreOS(unittest.TestCase):
    func_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    assets_path = "%s/bootcfg/assets" % project_path
    asset_test = "%s/coreos" % assets_path
    default_files = ["Makefile"]
    version = default_files + ["1214.0.0"]

    def test_00_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_01_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_02_serve(self):
        expect = self.version + ["serve"]
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

    def test_05_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_06_serve(self):
        expect = self.version + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "serve"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)


@unittest.skipIf(os.getenv("PYCHARM_HOSTED"), "PYCHARM_HOSTED")
class TestAssetsCNI(unittest.TestCase):
    func_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    assets_path = "%s/bootcfg/assets" % project_path
    asset_test = "%s/cni" % assets_path
    default_files = ["Makefile"]
    version = default_files

    def test_00_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_01_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_02_serve(self):
        expect = self.version + ["serve"]
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

    def test_05_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_06_serve(self):
        expect = self.version + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "serve"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)


@unittest.skipIf(os.getenv("PYCHARM_HOSTED"), "PYCHARM_HOSTED")
class TestAssetsSetupNetworkEnvironment(unittest.TestCase):
    func_path = "%s" % os.path.dirname(__file__)
    tests_path = os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    assets_path = "%s/bootcfg/assets" % project_path
    asset_test = "%s/setup-network-environment" % assets_path
    default_files = ["Makefile", "1.0.1-setup-network-environment.sha512"]
    version = default_files + ["1.0.1"]

    def test_00_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_01_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_02_serve(self):
        expect = self.version + ["serve"]
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

    def test_05_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_06_serve(self):
        expect = self.version + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "serve"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)


@unittest.skipIf(os.getenv("PYCHARM_HOSTED"), "PYCHARM_HOSTED")
class TestAssetsRkt(unittest.TestCase):
    func_path = "%s" % os.path.dirname(__file__)
    tests_path = os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    assets_path = "%s/bootcfg/assets" % project_path
    asset_test = "%s/rkt" % assets_path
    default_files = ["Makefile"]
    version = default_files + ["v1.19.0"]

    def test_00_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_01_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_02_serve(self):
        expect = self.version + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "serve"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_03_clean(self):
        expect = self.version + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "clean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_04_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_05_default(self):
        expect = self.version
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_06_serve(self):
        expect = self.version + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test, "serve"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)


@unittest.skipIf(os.getenv("PYCHARM_HOSTED"), "PYCHARM_HOSTED")
class TestAssetsDiscoveryC(unittest.TestCase):
    func_path = "%s" % os.path.dirname(__file__)
    tests_path = os.path.split(func_path)[0]
    app_path = os.path.split(tests_path)[0]
    project_path = os.path.split(app_path)[0]
    assets_path = "%s/bootcfg/assets" % project_path
    asset_test = "%s/discoveryC" % assets_path
    default_files = ["Makefile"]

    def test_00_fclean(self):
        expect = self.default_files
        subprocess.check_output(["make", "-C", self.asset_test, "fclean"])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_01_default(self):
        expect = self.default_files + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_02_static(self):
        f = "%s/serve/discoveryC" % self.asset_test
        self.assertTrue(os.path.isfile(f))
        ret = subprocess.call(["ldd", f])
        self.assertEqual(ret, 1)

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

    def test_05_default(self):
        expect = self.default_files + ["serve"]
        subprocess.check_output(["make", "-C", self.asset_test])
        real = os.listdir(self.asset_test)
        self.assertItemsEqual(expect, real)

    def test_06_static(self):
        f = "%s/serve/discoveryC" % self.asset_test
        self.assertTrue(os.path.isfile(f))
        ret = subprocess.call(["ldd", f])
        self.assertEqual(ret, 1)
