import os
import time
import urllib2

import requests
from flask import Flask, request, json, jsonify, render_template
from sqlalchemy import create_engine
from werkzeug.contrib.cache import SimpleCache

import crud
import logger
import model
import backup
from configs import EnjoliverConfig

ec = EnjoliverConfig()

LOGGER = logger.get_logger(__file__)

app = application = Flask(__name__)
cache = SimpleCache()

application.config["BOOTCFG_URI"] = ec.bootcfg_uri
application.config["API_URI"] = ec.api_uri

application.config["BOOTCFG_URLS"] = ec.bootcfg_urls

application.config["DB_PATH"] = ec.db_path
application.config["DB_URI"] = ec.db_uri

ignition_journal = application.config["IGNITION_JOURNAL_DIR"] = ec.ignition_journal_dir

application.config["BACKUP_BUCKET_NAME"] = ec.backup_bucket_name
application.config["BACKUP_BUCKET_DIRECTORY"] = ec.backup_bucket_directory
application.config["BACKUP_LOCK_KEY"] = ec.backup_lock_key

engine = None

if __name__ == '__main__' or "gunicorn" in os.getenv("SERVER_SOFTWARE", "foreign"):
    for k, v in ec.__dict__.iteritems():
        LOGGER.info("<config> %s=%s" % (k, v))

    # Start the db
    LOGGER.info("Create engine %s" % application.config["DB_URI"])
    engine = create_engine(application.config["DB_URI"])
    LOGGER.info("Create model %s" % application.config["DB_URI"])
    model.Base.metadata.create_all(engine)
    LOGGER.info("Engine with <driver: %s> " % engine.driver)


@application.route("/config", methods=["GET"])
def config():
    return jsonify(ec.__dict__)


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

    while cache.get(application.config["BACKUP_LOCK_KEY"]) is not None:
        app.logger.debug("Cache backup is not None")
        time.sleep(0.1)

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
    fetch = crud.FetchSchedule(
        engine=engine,
    )
    all_sch = fetch.get_schedules()
    fetch.close()

    return jsonify(all_sch)


@application.route('/scheduler/<string:role>', methods=['GET'])
def get_schedule_by_role(role):
    fetch = crud.FetchSchedule(
        engine=engine,
    )
    multi = role.split("&")
    data = fetch.get_roles(*multi)
    fetch.close()

    return jsonify(data)


@application.route('/scheduler/available', methods=['GET'])
def get_available_machine():
    fetch = crud.FetchSchedule(
        engine=engine,
    )
    data = fetch.get_available_machines()
    fetch.close()

    return jsonify(data)


@application.route('/scheduler/ip-list/<string:role>', methods=['GET'])
def get_schedule_role_ip_list(role):
    fetch = crud.FetchSchedule(
        engine=engine,
    )
    ip_list_role = fetch.get_role_ip_list(role)
    fetch.close()

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
    return backup.backup_sqlite(cache=cache, application=application)


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
