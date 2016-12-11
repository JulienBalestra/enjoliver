import os

import time
from boto.s3.connection import S3Connection
from boto.s3.key import Key


class S3Operator(object):
    def __init__(self, bucket_name):
        aws_id = os.getenv("AWS_ACCESS_KEY_ID", None)
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", None)

        if aws_id is None or aws_secret is None:
            raise EnvironmentError("Missing the couple AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY")

        self.conn = S3Connection(
            aws_access_key_id=aws_id,
            aws_secret_access_key=aws_secret)
        self.bucket = self.conn.get_bucket(bucket_name)

    def upload(self, source, dest, override=True):
        if override is False:
            key = Key(self.bucket, dest)
            if key.exists() is True:
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
            key.set_metadata(k, v)
        print key.metadata
        key.set_contents_from_filename(source)

    def download(self, source, dest):
        key = Key(self.bucket, source)
        key.get_contents_to_filename(dest)

    def get_last_uploaded(self, prefix):
        keys = []
        for item in self.bucket.list(prefix=prefix):
            key = self.bucket.get_key(key_name=item)
            key.get_metadata("uploaded")
            keys.append(key)

        keys.sort(key=lambda x: x.metadata["uploaded"])
        latest = keys[0]

        return latest.key
