import ctypes
import math
import os
import shutil
import time

from flask import jsonify

import s3

libc = ctypes.CDLL("libc.so.6")  # TODO deep inside the SQLITE sync


def backup_sqlite(cache, application):
    """
    Backup the db by copying it and uploading to a S3 bucket
    During the copy of the db a key is set inside the werkzeug cache to avoid writes
        This key have a TTL and is always unset whatever the status of the backup
    The application config contains the needed keys for the operation:
        - BACKUP_BUCKET_NAME
        - BACKUP_BUCKET_DIRECTORY
        - DB_PATH
        - BACKUP_LOCK_KEY
    :return: Summary of the operation ; copy and upload keys summarize the result success
    """
    start = time.time()
    now_rounded = int(math.ceil(start))
    dest_s3 = "%s/%s.db" % (application.config["BACKUP_BUCKET_DIRECTORY"], now_rounded)
    db_path = application.config["DB_PATH"]
    bucket_name = application.config["BACKUP_BUCKET_NAME"]
    b = {
        "copy": False,
        "upload": False,
        "source_fs": db_path,
        "dest_fs": "%s-%s.bak" % (db_path, now_rounded),
        "dest_s3": dest_s3 if bucket_name else None,
        "bucket_name": bucket_name,
        "bucket_uri": "s3://%s/%s" % (bucket_name, dest_s3) if application.config[
            "BACKUP_BUCKET_NAME"] else None,
        "size": None,
        "ts": now_rounded,
        "backup_duration": None,
        "lock_duration": None,
        "already_locked": False,
    }
    if cache.get(application.config["BACKUP_LOCK_KEY"]):
        b["already_locked"] = True
        return jsonify(b)

    try:
        source_st = os.stat(b["source_fs"])
        timeout = math.ceil(source_st.st_size / (1024 * 1024.))
        application.logger.info("Backup lock key set with timeout == %ss" % timeout)
        cache.set(application.config["BACKUP_LOCK_KEY"], b["dest_fs"], timeout=timeout)
        libc.sync()
        shutil.copy2(db_path, b["dest_fs"])
        dest_st = os.stat(b["dest_fs"])
        b["size"], b["copy"] = dest_st.st_size, True
    except Exception as e:
        application.logger.error("<%s %s>: %s" % (e, type(e), e.message))
    finally:
        cache.delete(application.config["BACKUP_LOCK_KEY"])
        b["lock_duration"] = time.time() - start
        application.logger.debug("lock duration: %ss" % b["lock_duration"])

    try:
        if b["copy"] is False:
            application.logger.error("copy is False: %s" % b["dest_fs"])
            raise IOError(b["dest_fs"])

        so = s3.S3Operator(b["bucket_name"])
        so.upload(b["dest_fs"], b["dest_s3"])
        b["upload"] = True
    except Exception as e:
        application.logger.error("<%s %s>: %s" % (e, type(e), e.message))

    b["backup_duration"] = time.time() - start
    application.logger.info("backup duration: %ss" % b["backup_duration"])
    return jsonify(b)
