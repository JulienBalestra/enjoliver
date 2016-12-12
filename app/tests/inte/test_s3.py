import os
import unittest

import shutil
import json

from app import s3

try:
    with open("%s/.config/enjoliver/config.json" % os.getenv("HOME")) as f:
        conf = json.load(f)
        os.environ["AWS_ACCESS_KEY_ID"] = conf["AWS_ACCESS_KEY_ID"]
        os.environ["AWS_SECRET_ACCESS_KEY"] = conf["AWS_SECRET_ACCESS_KEY"]
except (IOError, ValueError):
    pass


@unittest.skipIf(os.getenv("AWS_ACCESS_KEY_ID") is None, "Missing env AWS_ACCESS_KEY_ID")
@unittest.skipIf(os.getenv("AWS_SECRET_ACCESS_KEY") is None, "Missing env AWS_SECRET_ACCESS_KEY")
class TestS3Operator(unittest.TestCase):
    testing_bucket = "bbcenjoliver-dev"

    inte_path = os.path.dirname(os.path.abspath(__file__))
    s3_resource_dir_name = "test_resources"
    s3_resource_dir = os.path.join(inte_path, s3_resource_dir_name)

    @classmethod
    def setUpClass(cls):
        cls.so = s3.S3Operator(cls.testing_bucket)
        try:
            shutil.rmtree(cls.s3_resource_dir)
        except OSError:
            pass
        os.makedirs(cls.s3_resource_dir)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_00(self):
        test_file = os.path.join(self.s3_resource_dir, "%s" % self.test_00.__name__)
        with open(test_file, "w") as f:
            f.write("data from %s" % self.test_00.__name__)
        key = "%s/%s" % (
            self.s3_resource_dir_name, self.test_00.__name__)
        self.so.upload(test_file, key)
        downloaded = "%s.downloaded" % test_file
        self.so.download(key, downloaded)
        with open(downloaded, 'r') as d, open(test_file, 'r') as s:
            self.assertEqual(d.read(), s.read())
        with self.assertRaises(IOError):
            self.so.upload(test_file, key, override=False)

    def test_01(self):
        test_file = os.path.join(self.s3_resource_dir, "%s" % self.test_01.__name__)
        with open(test_file, "w") as f:
            f.write("data from %s" % self.test_01.__name__)
        key = "%s/%s" % (
            self.s3_resource_dir_name, self.test_01.__name__)
        self.so.upload(test_file, key)
        latest = self.so.get_last_uploaded(self.s3_resource_dir_name)
        self.assertEqual(key, latest)

