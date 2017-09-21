"""
Interface with S3 to store / fetch backups
"""
import os
import time

import boto3
import logging
from configs import EnjoliverConfig

logger = logging.getLogger(__name__)


class S3Operator(object):
    def __init__(self, bucket_name):
        ec = EnjoliverConfig(importer=__file__)
        aws_id = ec.aws_id
        aws_secret = ec.aws_secret
        self.bucket_name = bucket_name

        if not bucket_name:
            logger.error("bucket_name=%s" % bucket_name)
            raise AttributeError("bucket_name is not defined: %s" % bucket_name)

        if aws_id is None or aws_secret is None:
            logger.error("Missing the couple AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY")
            raise EnvironmentError("Missing the couple AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY")
        logger.info("connect to bucket name: %s" % bucket_name)

        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(bucket_name)

    def upload(self, source, dest):
        if os.path.isfile(source) is False:
            raise IOError(source)
        obj = self.s3.Object(self.bucket_name, dest)

        stats = os.stat(source)
        metadata = {
            "uploaded": "%d" % time.time(),
            "created": "%d" % stats.st_ctime,
            "modified": "%d" % stats.st_mtime,
            "size": "%d" % stats.st_size
        }
        obj.put(Body=open(source, 'rb'), Metadata=metadata)
        logger.info("upload done source: %s dest: %s metadata: %s" % (source, dest, metadata))

    def download(self, source, dest):
        obj = self.s3.Object(self.bucket_name, source)
        r = obj.get(dest)
        with open(dest, 'wb') as f:
            f.write(r['Body']._raw_stream.data)
        logger.info("download done source: %s source: %s" % (source, dest))

    def get_last_uploaded(self, prefix):
        keys = []
        logger.debug("prefix use %s" % prefix)
        for item in self.bucket.objects.all():
            logger.debug("list in bucket: %s" % item.key)
            keys.append({"key": item.key, "last_modified": item.last_modified})

        keys.sort(key=lambda k: k["last_modified"])
        keys.reverse()
        latest = keys[0]
        key_name = latest["key"]
        logger.info("return latest upload: %s" % key_name)
        return key_name
