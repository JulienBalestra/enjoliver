import os
import time
import urllib2

import psutil
import requests
from flask import Flask, request, json, jsonify, render_template, Response
from sqlalchemy import create_engine

import backup
import crud
import logger
import model
from configs import EnjoliverConfig

ec = EnjoliverConfig()

if "werkzeug_cache" in ec.__dict__ and ec.werkzeug_cache == "SimpleCache":
    from werkzeug.contrib.cache import SimpleCache

    cache = SimpleCache()
else:
    from werkzeug.contrib.cache import FileSystemCache

    cache = FileSystemCache("/tmp/werkzeug-cache")

LOGGER = logger.get_logger(__file__)

app = application = Flask(__name__)

application.config["MATCHBOX_URI"] = ec.matchbox_uri
application.config["API_URI"] = ec.api_uri

application.config["MATCHBOX_URLS"] = ec.matchbox_urls

application.config["DB_PATH"] = ec.db_path
application.config["DB_URI"] = ec.db_uri

ignition_journal = application.config["IGNITION_JOURNAL_DIR"] = ec.ignition_journal_dir

application.config["BACKUP_BUCKET_NAME"] = ec.backup_bucket_name
application.config["BACKUP_BUCKET_DIRECTORY"] = ec.backup_bucket_directory
application.config["BACKUP_LOCK_KEY"] = ec.backup_lock_key

engine = None

if __name__ == '__main__' or "gunicorn" in os.getenv("SERVER_SOFTWARE", "_"):
    # Start the db engine
    LOGGER.info("Create engine %s" % application.config["DB_URI"])
    engine = create_engine(application.config["DB_URI"])
    LOGGER.info("Engine with <driver: %s> " % engine.driver)
    LOGGER.info("Clear the cache")
    cache.clear()


@application.route("/shutdown", methods=["POST"])
def shutdown():
    LOGGER.warning("shutdown asked")
    backup.backup_sqlite(cache=cache, application=application)
    pid_files = [ec.plan_pid_file, ec.matchbox_pid_file]
    gunicorn_pid = None
    pid_list = []

    for pid_file in pid_files:
        try:
            with open(pid_file) as f:
                pid_list.append(int(f.read()))
        except IOError:
            LOGGER.error("IOError -> %s" % pid_file)

    try:
        with open(ec.gunicorn_pid_file) as f:
            gunicorn_pid = int(f.read())
    except IOError:
        LOGGER.error("IOError -> %s" % ec.gunicorn_pid_file)

    for i, pid in enumerate(pid_list):
        try:
            p = psutil.Process(pid)
            LOGGER.warning("SIGTERM -> %d" % pid)
            p.terminate()
            LOGGER.warning("wait -> %d" % pid)
            p.wait()
            LOGGER.warning("%d running: %s " % (pid, p.is_running()))
        except psutil.NoSuchProcess:
            LOGGER.error("%d already dead" % pid)

    pid_list.append(gunicorn_pid)
    p = psutil.Process(gunicorn_pid)
    p.terminate()
    return Response("SIGTERM to %s\n" % pid_list, status=200, mimetype="text/plain")


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
        "matchbox": {k: False for k in application.config["MATCHBOX_URLS"]}
    }
    if app.config["MATCHBOX_URI"] is None:
        application.logger.error("MATCHBOX_URI is None")
    for k in status["matchbox"]:
        try:
            r = requests.get("%s%s" % (app.config["MATCHBOX_URI"], k))
            r.close()
            status["matchbox"][k] = True
        except Exception as e:
            status["matchbox"][k] = False
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
        app.logger.warning("Cache backup is not None")
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
    Replace the matchbox/boot.ipxe by insert retry for dhcp and full URL for the chain
    :return: str
    """
    try:
        flask_uri = application.config["API_URI"]
        if flask_uri is None:
            raise AttributeError("API_URI is None")
        app.logger.debug("%s" % flask_uri)

    except Exception as e:
        flask_uri = application.config["MATCHBOX_URI"]
        app.logger.error("<%s %s>: %s" % (e, type(e), e.message))
        app.logger.warning("Fall back to MATCHBOX_URI: %s" % flask_uri)
        if flask_uri is None:
            raise AttributeError("BOTH API_URI and MATCHBOX_URI are None")

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
    return Response(response, status=200, mimetype="text/plain")


@application.route("/ignition", methods=["GET"])
def ignition():
    matchbox_uri = application.config.get("MATCHBOX_URI")
    if matchbox_uri:
        matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
        d = matchbox_resp.content
        matchbox_resp.close()
        return Response(d, status=matchbox_resp.status_code, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@application.route("/metadata", methods=["GET"])
def metadata():
    matchbox_uri = application.config.get("MATCHBOX_URI")
    if matchbox_uri:
        matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
        d = matchbox_resp.content
        matchbox_resp.close()
        return Response(d, status=matchbox_resp.status_code, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@app.route('/assets', defaults={'path': ''})
@app.route('/assets/<path:path>')
def assets(path):
    matchbox_uri = application.config.get("MATCHBOX_URI")
    if matchbox_uri:
        url = "%s/assets/%s" % (matchbox_uri, path)
        matchbox_resp = requests.get(url)
        d = matchbox_resp.content
        matchbox_resp.close()
        return Response(response=d, mimetype="application/octet-stream")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@application.route('/ipxe', methods=['GET'])
def ipxe():
    """
    Fetch the matchbox/ipxe?<key>=<value> and insert retry for dhcp
    :return: str
    """
    try:
        matchbox_resp = urllib2.urlopen(
            "%s%s" % (
                app.config["MATCHBOX_URI"],
                request.full_path))
        resp_list = matchbox_resp.readlines()
        matchbox_resp.close()
        if len(resp_list) == 4:
            resp_list.insert(1, "echo start /ipxe\n")
        else:
            app.logger.warning("iPXE response is not coherent")

        response = "".join(resp_list)
        app.logger.debug("%s" % response)
        return Response(response, status=200, mimetype="text/plain")

    except urllib2.URLError:
        app.logger.warning("404")
        return Response("404", status=404, mimetype="text/plain")


@app.errorhandler(404)
def page_not_found(error):
    return Response("404", status=404, mimetype="text/plain")


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
