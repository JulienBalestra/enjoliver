import requests
from flask import Flask, request, json, jsonify, render_template, Response
from werkzeug.contrib.cache import FileSystemCache

import crud
import logger
import model
import ops
from configs import EnjoliverConfig
from smartdb import SmartClient

EC = EnjoliverConfig(importer=__file__)

CACHE = FileSystemCache(EC.werkzeug_fs_cache_dir)

LOGGER = logger.get_logger(__file__)

APP = APPLICATION = Flask(__name__)

APPLICATION.config["MATCHBOX_URI"] = EC.matchbox_uri
APPLICATION.config["API_URI"] = EC.api_uri

APPLICATION.config["MATCHBOX_URLS"] = EC.matchbox_urls

APPLICATION.config["DB_PATH"] = EC.db_path
APPLICATION.config["DB_URI"] = EC.db_uri

ignition_journal = APPLICATION.config["IGNITION_JOURNAL_DIR"] = EC.ignition_journal_dir

APPLICATION.config["BACKUP_BUCKET_NAME"] = EC.backup_bucket_name
APPLICATION.config["BACKUP_BUCKET_DIRECTORY"] = EC.backup_bucket_directory
APPLICATION.config["BACKUP_LOCK_KEY"] = EC.backup_lock_key

APPLICATION.config["SMART_CLIENT"] = SmartClient(APPLICATION.config["DB_URI"])
SMART = APPLICATION.config["SMART_CLIENT"]


@APPLICATION.route("/shutdown", methods=["POST"])
def shutdown():
    return ops.shutdown(EC)


@APPLICATION.route("/configs", methods=["GET"])
def configs():
    return jsonify(EC.__dict__)


@APPLICATION.route("/lifecycle/ignition/<string:request_raw_query>", methods=["POST"])
def submit_lifecycle_ignition(request_raw_query):
    try:
        machine_ignition = json.loads(request.get_data())
    except ValueError:
        LOGGER.error("%s have incorrect content" % request.path)
        return "FlaskValueError", 406
    req = requests.get("%s/ignition?%s" % (EC.matchbox_uri, request_raw_query))
    try:
        matchbox_ignition = json.loads(req.content)
        req.close()
    except ValueError:
        LOGGER.error("%s have incorrect matchbox return" % request.path)
        return "MatchboxValueError", 406

    with SMART.connected_session() as session:
        inject = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
        if json.dumps(machine_ignition, sort_keys=True) == json.dumps(matchbox_ignition, sort_keys=True):
            inject.refresh_lifecycle_ignition(True)
            resp = "Up-to-date", 200
        else:
            inject.refresh_lifecycle_ignition(False)
            resp = "Outdated", 210
    return resp


@APPLICATION.route("/lifecycle/rolling/<string:request_raw_query>", methods=["GET"])
def report_lifecycle_rolling(request_raw_query):
    with SMART.connected_session() as session:
        life = crud.FetchLifecycle(session)
        mac = crud.InjectLifecycle.get_mac_from_raw_query(request_raw_query)
        allow = life.get_rolling_status(mac)

        if allow is True:
            return "Enabled %s" % mac, 200
        elif allow is False:
            return "Disable %s" % mac, 403

    return "ForeignDisabled %s" % mac, 401


@APPLICATION.route("/lifecycle/rolling/<string:request_raw_query>", methods=["POST"])
def change_lifecycle_rolling(request_raw_query):
    LOGGER.info("%s %s" % (request.method, request.url))
    with SMART.connected_session() as session:
        try:
            life = crud.InjectLifecycle(session, request_raw_query)
            life.apply_lifecycle_rolling(True)
            status = "Enabled %s" % life.mac, 200
        except AttributeError:
            status = "Unknown in db %s" % request_raw_query, 401
    return status


@APPLICATION.route("/lifecycle/rolling/<string:request_raw_query>", methods=["DELETE"])
def lifecycle_rolling_delete(request_raw_query):
    LOGGER.info("%s %s" % (request.method, request.url))
    with SMART.connected_session() as session:
        life = crud.InjectLifecycle(session, request_raw_query)
        life.apply_lifecycle_rolling(False)
        report = "Disabled %s" % life.mac, 200
    return report


@APPLICATION.route("/lifecycle/rolling", methods=["GET"])
def lifecycle_rolling_all():
    with SMART.connected_session() as session:
        fetch = crud.FetchLifecycle(session)
        rolling_status_list = fetch.get_all_rolling_status()

    return jsonify(rolling_status_list)


@APPLICATION.route("/lifecycle/ignition", methods=["GET"])
def lifecycle_get_ignition_status():
    with SMART.connected_session() as session:
        fetch = crud.FetchLifecycle(session)
        updated_status_list = fetch.get_all_updated_status()

    return jsonify(updated_status_list)


@APPLICATION.route("/lifecycle/coreos-install", methods=["GET"])
def lifecycle_get_coreos_install_status():
    with SMART.connected_session() as session:
        fetch = crud.FetchLifecycle(session)
        install_status_list = fetch.get_all_coreos_install_status()

    return jsonify(install_status_list)


@APPLICATION.route("/lifecycle/coreos-install/<string:status>/<string:request_raw_query>", methods=["POST"])
def report_lifecycle_coreos_install(status, request_raw_query):
    LOGGER.info("%s %s" % (request.method, request.url))
    if status.lower() == "success":
        success = True
    elif status.lower() == "fail":
        success = False
    else:
        LOGGER.error("%s %s" % (request.method, request.url))
        return "success or fail != %s" % status.lower(), 403
    with SMART.connected_session() as session:
        inject = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
        inject.refresh_lifecycle_coreos_install(success)
    return "%s" % status, 200


@APPLICATION.route('/', methods=['GET'])
def root():
    """
    Map the API
    :return: available routes
    """
    rules = [k.rule for k in APPLICATION.url_map.iter_rules()]
    rules = list(set(rules))
    rules.sort()
    return jsonify(rules)


@APPLICATION.route('/healthz', methods=['GET'])
def healthz():
    resp = ops.healthz(APPLICATION, SMART, request)
    return jsonify(resp)


@APPLICATION.route('/discovery', methods=['POST'])
def discovery():
    LOGGER.info("%s %s" % (request.method, request.url))
    err = jsonify({u'boot-info': {}, u'lldp': {}, u'interfaces': []}), 406
    try:
        req = json.loads(request.get_data())
    except (KeyError, TypeError, ValueError):
        return err

    with SMART.connected_session() as session:
        try:
            inject = crud.InjectDiscovery(
                session,
                ignition_journal=ignition_journal,
                discovery=req)
            new = inject.commit()
            CACHE.delete(request.path)
            resp = jsonify({"total_elt": new[0], "new": new[1]})
        except TypeError:
            resp = err
    return resp


@APPLICATION.route('/discovery', methods=['GET'])
def discovery_get():
    all_data = CACHE.get(request.path)
    if all_data is None:
        with SMART.connected_session() as session:
            fetch = crud.FetchDiscovery(session, ignition_journal=ignition_journal)
            all_data = fetch.get_all()
            CACHE.set(request.path, all_data, timeout=30)
    return jsonify(all_data)


@APPLICATION.route('/scheduler', methods=['GET'])
def scheduler_get():
    all_data = CACHE.get(request.path)
    if all_data is None:
        with SMART.connected_session() as session:
            fetch = crud.FetchSchedule(session)
            all_data = fetch.get_schedules()
            CACHE.set(request.path, all_data, timeout=30)

    return jsonify(all_data)


@APPLICATION.route('/scheduler/<string:role>', methods=['GET'])
def get_schedule_by_role(role):
    with SMART.connected_session() as session:
        fetch = crud.FetchSchedule(session)
        multi = role.split("&")
        data = fetch.get_roles(*multi)

    return jsonify(data)


@APPLICATION.route('/scheduler/available', methods=['GET'])
def get_available_machine():
    with SMART.connected_session() as session:
        fetch = crud.FetchSchedule(session)
        data = fetch.get_available_machines()

    return jsonify(data)


@APPLICATION.route('/scheduler/ip-list/<string:role>', methods=['GET'])
def get_schedule_role_ip_list(role):
    with SMART.connected_session() as session:
        fetch = crud.FetchSchedule(session)
        ip_list_role = fetch.get_role_ip_list(role)

    return jsonify(ip_list_role)


@APPLICATION.route('/scheduler', methods=['POST'])
def scheduler_post():
    try:
        req = json.loads(request.get_data())
    except ValueError:
        return jsonify(
            {
                u"roles": model.ScheduleRoles.roles,
                u'selector': {
                    u"mac": ""
                }
            }), 406

    with SMART.connected_session() as session:
        inject = crud.InjectSchedule(session, data=req)
        inject.apply_roles()
        inject.commit()

    CACHE.delete(request.path)
    return jsonify(req)


@APPLICATION.route('/backup/db', methods=['POST'])
def backup_database():
    if "sqlite://" in EC.db_uri:
        return ops.backup_sqlite(cache=CACHE, application=APPLICATION)
    return jsonify({"NotImplementedError": "%s" % EC.api_uri}), 404


@APPLICATION.route('/discovery/interfaces', methods=['GET'])
def discovery_interfaces():
    with SMART.connected_session() as session:
        fetch = crud.FetchDiscovery(session, ignition_journal=ignition_journal)
        interfaces = fetch.get_all_interfaces()

    return jsonify(interfaces)


@APPLICATION.route('/discovery/ignition-journal/<string:uuid>/<string:boot_id>', methods=['GET'])
def discovery_ignition_journal_by_boot_id(uuid, boot_id):
    with SMART.connected_session() as session:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal(uuid, boot_id=boot_id)

    return jsonify(lines)


@APPLICATION.route('/discovery/ignition-journal/<string:uuid>', methods=['GET'])
def discovery_ignition_journal_by_uuid(uuid):
    with SMART.connected_session() as session:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal(uuid)

    return jsonify(lines)


@APPLICATION.route('/discovery/ignition-journal', methods=['GET'])
def discovery_ignition_journal_summary():
    with SMART.connected_session() as session:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal_summary()

    return jsonify(lines)


@APPLICATION.route('/boot.ipxe', methods=['GET'])
@APPLICATION.route('/boot.ipxe.0', methods=['GET'])
def boot_ipxe():
    """
    Replace the matchbox/boot.ipxe by insert retry for dhcp and full URL for the chain
    :return: str
    """
    LOGGER.info("%s %s" % (request.method, request.url))
    try:
        flask_uri = APPLICATION.config["API_URI"]
        if flask_uri is None:
            raise AttributeError("API_URI is None")
        APP.logger.debug("%s" % flask_uri)

    except Exception as e:
        flask_uri = APPLICATION.config["MATCHBOX_URI"]
        APP.logger.error("<%s %s>" % (e, type(e)))
        APP.logger.warning("Fall back to MATCHBOX_URI: %s" % flask_uri)
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
    return Response(response, status=200, mimetype="text/plain")


@APPLICATION.route("/ignition", methods=["GET"])
def ignition():
    matchbox_uri = APPLICATION.config.get("MATCHBOX_URI")
    if matchbox_uri:
        matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
        resp = matchbox_resp.content
        matchbox_resp.close()
        return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@APPLICATION.route("/metadata", methods=["GET"])
def metadata():
    matchbox_uri = APPLICATION.config.get("MATCHBOX_URI")
    if matchbox_uri:
        matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
        resp = matchbox_resp.content
        matchbox_resp.close()
        return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@APP.route('/install-authorization/<string:request_raw_query>')
def require_install_authorization(request_raw_query):
    """
    Used to avoid burst of
    :param request_raw_query:
    :return:
    """
    LOGGER.info("%s %s %s" % (request.method, request.remote_addr, request.url))
    if EC.coreos_install_lock_seconds > 0:
        lock = CACHE.get("lock-install")
        if lock is not None:
            LOGGER.warning("Locked by %s" % lock)
            return Response(response="Locked by %s" % lock, status=403)
        CACHE.set("lock-install", request_raw_query, timeout=EC.coreos_install_lock_seconds)
        LOGGER.info("Granted to %s" % request_raw_query)
    return Response(response="Granted", status=200)


@APP.route('/assets', defaults={'path': ''})
@APP.route('/assets/<path:path>')
def assets(path):
    LOGGER.info("%s %s" % (request.method, request.url))
    matchbox_uri = APPLICATION.config.get("MATCHBOX_URI")
    if matchbox_uri:
        url = "%s/assets/%s" % (matchbox_uri, path)
        matchbox_resp = requests.get(url)
        resp = matchbox_resp.content
        matchbox_resp.close()
        return Response(response=resp, mimetype="application/octet-stream")

    return Response("matchbox=%s" % matchbox_uri, status=404, mimetype="text/plain")


@APPLICATION.route('/ipxe', methods=['GET'])
def ipxe():
    """
    Fetch the matchbox/ipxe?<key>=<value> and insert retry for dhcp
    :return: str
    """
    LOGGER.info("%s %s" % (request.method, request.url))
    try:
        matchbox_resp = requests.get(
            "%s%s" % (
                APP.config["MATCHBOX_URI"],
                request.full_path))
        matchbox_resp.close()
        response = matchbox_resp.content.decode()
        return Response(response, status=200, mimetype="text/plain")

    except requests.exceptions.ConnectionError:
        APP.logger.warning("404 for /ipxe")
        return "404", 404


@APP.errorhandler(404)
def page_not_found(error):
    return Response("404", status=404, mimetype="text/plain")


@APPLICATION.route('/ui', methods=['GET'])
def user_interface():
    return render_template("index.html")


@APPLICATION.route('/ui/view/machine', methods=['GET'])
def user_view_machine():
    with SMART.connected_session() as session:
        view = crud.FetchView(session)
        res = view.get_machines()

    return jsonify(res)


if __name__ == "__main__":
    APP.logger.setLevel("DEBUG")
    APPLICATION.run(debug=True)
