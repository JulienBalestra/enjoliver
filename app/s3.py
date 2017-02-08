import os
import time

from boto.s3.connection import S3Connection
from boto.s3.key import Key

import logger
from configs import EnjoliverConfig


class S3Operator(object):
    log = logger.get_logger(__file__)

    def __init__(self, bucket_name):
        ec = EnjoliverConfig()
        aws_id = ec.aws_id
        aws_secret = ec.aws_secret

        if not bucket_name:
            self.log.error("bucket_name=%s" % bucket_name)
            raise AttributeError("bucket_name is not defined: %s" % bucket_name)

        if aws_id is None or aws_secret is None:
            self.log.error("Missing the couple AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY")
            raise EnvironmentError("Missing the couple AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY")
        self.log.info("connect to bucket name: %s" % bucket_name)
        self.conn = S3Connection(
            aws_access_key_id=aws_id,
            aws_secret_access_key=aws_secret)
        self.bucket = self.conn.get_bucket(bucket_name)

    def upload(self, source, dest, override=True):
        if override is False:
            self.log.debug("s3 upload with override as False")
            key = Key(self.bucket, dest)
            if key.exists() is True:
                self.log.error("Already here: %s")
                raise IOError("Already here: %s" % dest)
        key = Key(self.bucket, dest)
        stats = os.stat(source)
        metadata = {
            "uploaded": time.time(),
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "size": stats.st_size
        }
        for k, v in metadata.iteritems():
            self.log.debug("setting metadata %s = %s" % (k, v))
            key.set_metadata(k, v)
        key.set_contents_from_filename(source)
        self.log.info("upload done source: %s dest: %s metadata: %s" % (source, dest, metadata))

    def download(self, source, dest):
        key = Key(self.bucket, source)
        key.get_contents_to_filename(dest)
        self.log.info("download done source: %s source: %s" % (source, dest))

    def get_last_uploaded(self, prefix):
        keys = []
        self.log.debug("prefix use %s" % prefix)
        for item in self.bucket.list(prefix=prefix):
            self.log.debug("list in bucket: %s" % item.key)
            key = self.bucket.get_key(key_name=item)
            key.get_metadata("uploaded")
            keys.append(key)

        keys.sort(key=lambda x: - float(x.metadata["uploaded"]))
        latest = keys[0]
        key_name = latest.key.name
        self.log.info("return latest upload: %s" % key_name)
        return key_name
