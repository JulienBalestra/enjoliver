import ctypes
import math
import os
import shutil
import time
import urllib2

import requests
from flask import Flask, request, json, jsonify, render_template
from sqlalchemy import create_engine
from werkzeug.contrib.cache import SimpleCache

import crud
import logger
import model
import s3

LOGGER = logger.get_logger(__file__)

app = application = Flask(__name__)
cache = SimpleCache()

application.config["BOOTCFG_URI"] = os.getenv(
    "BOOTCFG_URI", "http://127.0.0.1:8080")

application.config["API_URI"] = os.getenv(
    "API_URI", None)

application.config["BOOTCFG_URLS"] = [
    "/",
    "/boot.ipxe",
    "/boot.ipxe.0",
    "/assets",
    "/metadata"
]

application.config["DB_PATH"] = os.getenv(
    "DB_PATH", '%s/enjoliver.sqlite' % os.path.dirname(os.path.abspath(__file__)))

application.config["DB_URI"] = os.getenv(
    "DB_URI", 'sqlite:///%s' % application.config["DB_PATH"])

ignition_journal = application.config["IGNITION_JOURNAL_DIR"] = os.getenv(
    "IGNITION_JOURNAL_DIR", '%s/ignition_journal' % os.path.dirname(os.path.abspath(__file__)))

application.config["BACKUP_BUCKET_NAME"] = os.getenv(
    "BACKUP_BUCKET_NAME", "")

application.config["BACKUP_BUCKET_DIRECTORY"] = os.getenv(
    "BACKUP_BUCKET_DIRECTORY", "enjoliver")

application.config["BACKUP_LOCK_KEY"] = "backup_lock"

libc = ctypes.CDLL("libc.so.6")  # TODO deep inside the SQLITE sync
engine = None

if __name__ == '__main__' or "gunicorn" in os.getenv("SERVER_SOFTWARE", "foreign"):
    # API URI
    LOGGER.info("API_URI=%s" % application.config["API_URI"])

    # bootcfg == Coreos-Baremetal
    LOGGER.info("BOOTCFG_URI=%s" % application.config["BOOTCFG_URI"])
    LOGGER.info("BOOTCFG_URLS=%s" % application.config["BOOTCFG_URLS"])

    # Database config
    LOGGER.info("DB_PATH=%s" % application.config["DB_PATH"])
    LOGGER.info("DB_URI=%s" % application.config["DB_URI"])
    LOGGER.info("IGNITION_JOURNAL_DIR=%s" % application.config["IGNITION_JOURNAL_DIR"])

    # Backup
    LOGGER.info("BACKUP_BUCKET_NAME=%s" % application.config["BACKUP_BUCKET_NAME"])
    LOGGER.info("BACKUP_BUCKET_DIRECTORY=%s" % application.config["BACKUP_BUCKET_DIRECTORY"])
    LOGGER.info("AWS_ACCESS_KEY_ID=len(%d)" % len(os.getenv("AWS_ACCESS_KEY_ID", "")))
    LOGGER.info("AWS_SECRET_ACCESS_KEY=len(%d)" % len(os.getenv("AWS_SECRET_ACCESS_KEY", "")))
    LOGGER.info("BACKUP_LOCK_KEY=%s" % application.config["BACKUP_LOCK_KEY"])

    # Start the db
    LOGGER.info("Create engine %s" % application.config["DB_URI"])
    engine = create_engine(application.config["DB_URI"])
    LOGGER.info("Create model %s" % application.config["DB_URI"])
    model.Base.metadata.create_all(engine)
    LOGGER.info("Engine with <driver: %s> " % engine.driver)


@application.route("/config", methods=["GET"])
def config():
    wanted, c = [
                    "API_URI",
                    "BOOTCFG_URI",
                    "BOOTCFG_URLS",
                    "DB_PATH",
                    "DB_URI",
                    "IGNITION_JOURNAL_DIR",
                    "BACKUP_BUCKET_NAME",
                    "BACKUP_BUCKET_DIRECTORY",
                    "BACKUP_LOCK_KEY"
                ], dict()
    for elt in wanted:
        c[elt] = application.config[elt]
    return jsonify(c)


@application.route('/', methods=['GET'])
def root():
    """
    Map the API
    :return: available routes
    """
    r = [k.rule for k in application.url_map.iter_rules()]
    r = list(set(r))
    r.sort()
    return jsonify(r)


@application.route('/healthz', methods=['GET'])
def healthz():
    """
    Query all services and return the status
    :return: json
    """
    status = {
        "global": True,
        "flask": True,
        "db": False,
        "bootcfg": {k: False for k in application.config["BOOTCFG_URLS"]}
    }
    if app.config["BOOTCFG_URI"] is None:
        application.logger.error("BOOTCFG_URI is None")
    for k in status["bootcfg"]:
        try:
            r = requests.get("%s%s" % (app.config["BOOTCFG_URI"], k))
            r.close()
            status["bootcfg"][k] = True
        except Exception as e:
            status["bootcfg"][k] = False
            status["global"] = False
            LOGGER.error(e)
    try:
        status["db"] = crud.health_check(engine=engine, ts=time.time(), who=request.remote_addr)
    except Exception as e:
        status["global"] = False
        LOGGER.error(e)

    app.logger.debug("%s" % status)
    return json.jsonify(status)


@application.route('/discovery', methods=['POST'])
def discovery():
    if request.content_type != "application/json":
        try:
            r = json.loads(request.data)
        except ValueError:
            app.logger.error("ValueError for %s" % request.data)
            return jsonify(
                {
                    u'boot-info': {},
                    u'lldp': {},
                    u'interfaces': []
                }), 400
    else:
        r = request.get_json()

    app.logger.debug("application/json \"%s\"" % r)

    while cache.get(application.config["BACKUP_LOCK_KEY"]) is not None:
        app.logger.debug("Cache backup is not None")
        time.sleep(0.1)

    # Another logger
    LOGGER.debug(r)
    try:
        i = crud.InjectDiscovery(engine=engine,
                                 ignition_journal=ignition_journal,
                                 discovery=r)
        new = i.commit_and_close()
        cache.delete("discovery")
        return jsonify({"total_elt": new[0], "new": new[1]})

    except (KeyError, TypeError):
        return jsonify(
            {
                u'boot-info': {},
                u'lldp': {},
                u'interfaces': []
            }), 406


@application.route('/discovery', methods=['GET'])
def discovery_get():
    key = "discovery"
    all_data = cache.get(key)
    if all_data is None:
        fetch = crud.FetchDiscovery(
            engine=engine,
            ignition_journal=ignition_journal
        )
        all_data = fetch.get_all()
        cache.set(key, all_data, timeout=30)

    return jsonify(all_data)


@application.route('/scheduler', methods=['GET'])
def get_all_schedules():
    key = "schedules"
    all_sch = cache.get(key)
    if all_sch is None:
        fetch = crud.FetchSchedule(
            engine=engine,
        )
        all_sch = fetch.get_schedules()
        fetch.close()
        cache.set(key, all_sch, timeout=30)

    return jsonify(all_sch)


@application.route('/scheduler/<string:role>', methods=['GET'])
def get_schedule_by_role(role):
    data = cache.get(role)
    if data is None:
        fetch = crud.FetchSchedule(
            engine=engine,
        )
        multi = role.split("&")
        data = fetch.get_roles(*multi)
        fetch.close()
        cache.set(role, data, timeout=30)

    return jsonify(data)


@application.route('/scheduler/ip-list/<string:role>', methods=['GET'])
def get_schedule_role_ip_list(role):
    key = "ip-list-%s" % role
    ip_list_role = cache.get(key)
    if ip_list_role is None:
        fetch = crud.FetchSchedule(
            engine=engine,
        )
        ip_list_role = fetch.get_role_ip_list(role)
        fetch.close()
        cache.set(key, ip_list_role, timeout=30)

    return jsonify(ip_list_role)


@application.route('/scheduler', methods=['POST'])
def schedule_role():
    if request.content_type != "application/json":
        try:
            r = json.loads(request.get_data())
        except ValueError:
            app.logger.error("ValueError for %s" % request.data)
            return jsonify(
                {
                    u"roles": model.ScheduleRoles.roles,
                    u'selector': {
                        "mac": ""
                    }
                }), 400
    else:
        r = request.get_json()

    inject = crud.InjectSchedule(
        engine=engine,
        data=r)
    try:
        inject.apply_roles()
        cache.delete("schedules")
    finally:
        inject.commit_and_close()

    return jsonify(r)


@application.route('/backup/db', methods=['POST'])
def backup_database():
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
        app.logger.info("Backup lock key set with timeout == %ss" % timeout)
        cache.set(application.config["BACKUP_LOCK_KEY"], b["dest_fs"], timeout=timeout)
        libc.sync()
        shutil.copy2(db_path, b["dest_fs"])
        dest_st = os.stat(b["dest_fs"])
        b["size"], b["copy"] = dest_st.st_size, True
    except Exception as e:
        app.logger.error("<%s %s>: %s" % (e, type(e), e.message))
    finally:
        cache.delete(application.config["BACKUP_LOCK_KEY"])
        b["lock_duration"] = time.time() - start
        app.logger.debug("lock duration: %ss" % b["lock_duration"])

    try:
        if b["copy"] is False:
            app.logger.error("copy is False: %s" % b["dest_fs"])
            raise IOError(b["dest_fs"])

        so = s3.S3Operator(b["bucket_name"])
        so.upload(b["dest_fs"], b["dest_s3"])
        b["upload"] = True
    except Exception as e:
        app.logger.error("<%s %s>: %s" % (e, type(e), e.message))

    b["backup_duration"] = time.time() - start
    app.logger.info("backup duration: %ss" % b["backup_duration"])
    return jsonify(b)


@application.route('/discovery/interfaces', methods=['GET'])
def discovery_interfaces():
    fetch = crud.FetchDiscovery(engine=engine,
                                ignition_journal=ignition_journal)
    interfaces = fetch.get_all_interfaces()

    return jsonify(interfaces)


@application.route('/discovery/ignition-journal/<string:uuid>/<string:boot_id>', methods=['GET'])
def discovery_ignition_journal_by_boot_id(uuid, boot_id):
    fetch = crud.FetchDiscovery(engine=engine,
                                ignition_journal=ignition_journal)
    lines = fetch.get_ignition_journal(uuid, boot_id=boot_id)

    return jsonify(lines)


@application.route('/discovery/ignition-journal/<string:uuid>', methods=['GET'])
def discovery_ignition_journal_by_uuid(uuid):
    fetch = crud.FetchDiscovery(engine=engine,
                                ignition_journal=ignition_journal)
    lines = fetch.get_ignition_journal(uuid)

    return jsonify(lines)


@application.route('/discovery/ignition-journal', methods=['GET'])
def discovery_ignition_journal_summary():
    fetch = crud.FetchDiscovery(engine=engine,
                                ignition_journal=ignition_journal)
    lines = fetch.get_ignition_journal_summary()

    return jsonify(lines)


@application.route('/boot.ipxe', methods=['GET'])
@application.route('/boot.ipxe.0', methods=['GET'])
def boot_ipxe():
    """
    Replace the bootcfg/boot.ipxe by insert retry for dhcp and full URL for the chain
    :return: str
    """
    try:
        flask_uri = application.config["API_URI"]
        if flask_uri is None:
            raise AttributeError("API_URI is None")
        app.logger.debug("%s" % flask_uri)

    except Exception as e:
        flask_uri = application.config["BOOTCFG_URI"]
        app.logger.error("<%s %s>: %s" % (e, type(e), e.message))
        app.logger.warning("Fall back to BOOTCFG_URI: %s" % flask_uri)
        if flask_uri is None:
            raise AttributeError("BOTH API_URI and BOOTCFG_URI are None")

    response = \
        "#!ipxe\n" \
        "echo start /boot.ipxe\n" \
        ":retry_dhcp\n" \
        "dhcp || goto retry_dhcp\n" \
        "chain %s/ipxe?" \
        "uuid=${uuid}&" \
        "mac=${net0/mac:hexhyp}&" \
        "domain=${domain}&" \
        "hostname=${hostname}&" \
        "serial=${serial}\n" % flask_uri
    app.logger.debug("%s" % response)
    return response


@application.route("/ignition", methods=["GET"])
def ignition():
    bootcfg_uri = application.config.get("BOOTCFG_URI")
    if bootcfg_uri:
        bootcfg_resp = requests.get("%s%s" % (bootcfg_uri, request.full_path))
        d = bootcfg_resp.content
        bootcfg_resp.close()
        return d, bootcfg_resp.status_code

    return "bootcfg=%s" % bootcfg_uri, 403


@application.route("/metadata", methods=["GET"])
def metadata():
    bootcfg_uri = application.config.get("BOOTCFG_URI")
    if bootcfg_uri:
        bootcfg_resp = requests.get("%s%s" % (bootcfg_uri, request.full_path))
        d = bootcfg_resp.content
        bootcfg_resp.close()
        return d, bootcfg_resp.status_code

    return "bootcfg=%s" % bootcfg_uri, 403


@app.route('/assets', defaults={'path': ''})
@app.route('/assets/<path:path>')
def assets(path):
    bootcfg_uri = application.config.get("BOOTCFG_URI")
    if bootcfg_uri:
        url = "%s/assets/%s" % (bootcfg_uri, path)
        bootcfg_resp = requests.get(url)
        d = bootcfg_resp.content
        bootcfg_resp.close()
        return d, bootcfg_resp.status_code

    return "bootcfg=%s" % bootcfg_uri, 403


@application.route('/ipxe', methods=['GET'])
def ipxe():
    """
    Fetch the bootcfg/ipxe?<key>=<value> and insert retry for dhcp
    :return: str
    """
    try:
        bootcfg_resp = urllib2.urlopen(
            "%s%s" % (
                app.config["BOOTCFG_URI"],
                request.full_path))
        resp_list = bootcfg_resp.readlines()
        bootcfg_resp.close()
        if len(resp_list) == 4:
            resp_list.insert(1, "echo start /ipxe\n")
        else:
            app.logger.warning("iPXE response is not coherent")

        response = "".join(resp_list)
        app.logger.debug("%s" % response)
        return response, 200

    except urllib2.URLError:
        return "404", 404


@app.errorhandler(404)
def page_not_found(error):
    return '404\n', 404


@application.route('/ui', methods=['GET'])
def user_interface():
    return render_template("index.html")


@application.route('/ui/view/machine', methods=['GET'])
def user_view_machine():
    key = "discovery"
    all_data = cache.get(key)
    if all_data is None:
        fetch = crud.FetchDiscovery(
            engine=engine,
            ignition_journal=ignition_journal
        )
        all_data = fetch.get_all()
        cache.set(key, all_data, timeout=30)

    res = [["created-date", "updated-date", "uuid", "cidr-boot", "mac-boot"]]
    for i in all_data:
        sub_list = list()
        sub_list.append(i["boot-info"]["created-date"])
        sub_list.append(i["boot-info"]["updated-date"])
        sub_list.append(i["boot-info"]["uuid"])
        for j in i["interfaces"]:
            if j["as_boot"]:
                sub_list.append(j["cidrv4"])
                sub_list.append(j["mac"])
        res.append(sub_list)

    return jsonify(res)


if __name__ == "__main__":
    app.logger.setLevel("DEBUG")
    application.run(debug=True)
