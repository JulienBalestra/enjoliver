import json
import logging
import os
import sys
import time

import requests
from flasgger import Swagger
from flask import Flask, request, json, jsonify, render_template, Response, make_response
from werkzeug.contrib.cache import FileSystemCache

import crud
import model
import monitoring
import ops
import smartdb
import tools
from configs import EnjoliverConfig
from model import MachineStates
from repositories.register import RepositoriesRegister
from smartdb import SmartDatabaseClient

EC = EnjoliverConfig(importer=__file__)
CACHE = FileSystemCache(EC.werkzeug_fs_cache_dir)

logger = logging.getLogger(__name__)

app = application = Flask(__name__)
jinja_options = app.jinja_options.copy()
jinja_options.update(dict(
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='%%',
    variable_end_string='%%',
    comment_start_string='<#',
    comment_end_string='#>'
))
app.jinja_options = jinja_options

Swagger(app)

application.config["MATCHBOX_URI"] = EC.matchbox_uri
application.config["API_URI"] = EC.api_uri
application.config["MATCHBOX_URLS"] = EC.matchbox_urls
application.config["DB_PATH"] = EC.db_path
ignition_journal = application.config["IGNITION_JOURNAL_DIR"] = EC.ignition_journal_dir
application.config["BACKUP_BUCKET_NAME"] = EC.backup_bucket_name
application.config["BACKUP_BUCKET_DIRECTORY"] = EC.backup_bucket_directory
application.config["BACKUP_LOCK_KEY"] = EC.backup_lock_key

SMART = SmartDatabaseClient
# repositories
repositories = RepositoriesRegister

if __name__ == '__main__' or "gunicorn" in os.getenv("SERVER_SOFTWARE", ""):
    logging.basicConfig(level=EC.logging_level, stream=sys.stderr, format=EC.logging_formatter)
    fmt = logging.Formatter(EC.logging_formatter)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(fmt)
    app.logger.addHandler(handler)
    app.logger.setLevel(EC.logging_level)
    monitoring.monitor_flask(application)

    SMART = SmartDatabaseClient(EC.db_uri)
    # repositories
    repositories = RepositoriesRegister(SMART)


@application.route("/shutdown", methods=["POST"])
def shutdown():
    """
    Shutdown
    Shutdown the application
    ---
    tags:
      - ops
    responses:
      200:
        description: List of the state of each PIDs
    """
    return ops.shutdown(EC)


@application.route("/configs", methods=["GET"])
@application.route("/config", methods=["GET"])
def configs():
    """
    Configs
    Returns the current running configuration
    ---
    tags:
      - ops
    responses:
      200:
        description: A JSON of the configuration
    """
    return jsonify(EC.__dict__)


@application.route("/lifecycle/ignition/<string:request_raw_query>", methods=["POST"])
def submit_lifecycle_ignition(request_raw_query):
    """
    Lifecycle Ignition
    ---
    tags:
      - lifecycle
    responses:
      200:
        description: A JSON of the ignition status
    """
    try:
        machine_ignition = json.loads(request.get_data())
    except ValueError:
        app.logger.error("%s have incorrect content" % request.path)
        return jsonify({"message": "FlaskValueError"}), 406
    req = requests.get("%s/ignition?%s" % (EC.matchbox_uri, request_raw_query))
    try:
        matchbox_ignition = json.loads(req.content)
        req.close()
    except ValueError:
        app.logger.error("%s have incorrect matchbox return" % request.path)
        return jsonify({"message": "MatchboxValueError"}), 406

    @smartdb.cockroach_transaction
    def op(caller=request.url_rule):
        with SMART.new_session() as session:
            try:
                inject = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
                if json.dumps(machine_ignition, sort_keys=True) == json.dumps(matchbox_ignition, sort_keys=True):
                    inject.refresh_lifecycle_ignition(True)
                    return jsonify({"message": "Up-to-date"}), 200
                else:
                    inject.refresh_lifecycle_ignition(False)
                    return jsonify({"message": "Outdated"}), 210
            except AttributeError:
                return jsonify({"message": "Unknown"}), 406

    return op(caller=request.url_rule)


@application.route("/lifecycle/rolling/<string:request_raw_query>", methods=["GET"])
def report_lifecycle_rolling(request_raw_query):
    """
    Lifecycle Rolling Update
    Get the current policy for a given machine by UUID or MAC
    ---
    tags:
      - lifecycle
    parameters:
      - name: request_raw_query
        in: path
        description: Pass the mac as 'mac=<mac>'
        required: true
        type: string
    responses:
      403:
        description: mac address is not parsable
        schema:
            type: dict
      200:
        description: Rolling Update is enable
        schema:
            type: dict
      403:
        description: Rolling Update is not enable
        schema:
            type: dict
    """
    with SMART.new_session() as session:
        life = crud.FetchLifecycle(session)
        try:
            mac = tools.get_mac_from_raw_query(request_raw_query)
        except AttributeError as e:
            return jsonify({"enable": None, "request_raw_query": "%s:%s" % (request_raw_query, e)}), 403

        allow, strategy = life.get_rolling_status(mac)

        if allow is True:
            return jsonify({"enable": True, "request_raw_query": request_raw_query, "strategy": strategy}), 200
        elif allow is False:
            return jsonify({"enable": False, "request_raw_query": request_raw_query, "strategy": strategy}), 403

    return jsonify({"enable": False, "request_raw_query": request_raw_query, "strategy": None}), 401


@application.route("/lifecycle/rolling/<string:request_raw_query>", methods=["POST"])
def change_lifecycle_rolling(request_raw_query):
    """
    Lifecycle Rolling Update
    Change the current policy for a given machine by MAC
    ---
    tags:
      - lifecycle
    parameters:
      - name: request_raw_query
        in: path
        description: Pass the mac as 'mac=<mac>'
        required: true
        type: string
    responses:
      200:
        description: Rolling Update is enable
        schema:
            type: dict
      401:
        description: Mac address is not in database
        schema:
            type: dict
    """

    app.logger.info("%s %s" % (request.method, request.url))
    try:
        strategy = json.loads(request.get_data())["strategy"]
        app.logger.info("%s %s rolling strategy: setting to %s" % (request.method, request.url, strategy))
    except (KeyError, ValueError):
        # JSONDecodeError is a subclass of ValueError
        # Cannot use JSONDecodeError because the import is not consistent between python3.X
        app.logger.info("%s %s rolling strategy: setting default to kexec" % (request.method, request.url))
        strategy = "kexec"

    @smartdb.cockroach_transaction
    def op(caller=request.url_rule):
        with SMART.new_session() as session:
            try:
                life = crud.InjectLifecycle(session, request_raw_query)
                life.apply_lifecycle_rolling(True, strategy)
                return jsonify({"enable": True, "request_raw_query": request_raw_query, "strategy": strategy}), 200
            except AttributeError:
                return jsonify({"enable": None, "request_raw_query": request_raw_query, "strategy": strategy}), 401

    return op(caller=request.url_rule)


@application.route("/lifecycle/rolling/<string:request_raw_query>", methods=["DELETE"])
def lifecycle_rolling_delete(request_raw_query):
    """
    Lifecycle Rolling Update
    Disable the current policy for a given machine by UUID or MAC
    ---
    tags:
      - lifecycle
    parameters:
      - name: request_raw_query
        in: path
        description: Pass the mac as 'mac=<mac>'
        required: true
        type: string
    responses:
      200:
        description: Rolling Update is not enable
        schema:
            type: dict
    """
    app.logger.info("%s %s" % (request.method, request.url))

    @smartdb.cockroach_transaction
    def op(caller=request.url_rule):
        with SMART.new_session() as session:
            life = crud.InjectLifecycle(session, request_raw_query)
            life.apply_lifecycle_rolling(False, None)
            return jsonify({"enable": False, "request_raw_query": request_raw_query}), 200

    return op(caller=request.url_rule)


@application.route("/lifecycle/rolling", methods=["GET"])
def lifecycle_rolling_all():
    """
    Lifecycle Rolling Update
    Get the policy list
    ---
    tags:
      - lifecycle
    responses:
      200:
        description: Rolling Update status
        schema:
            type: list
    """
    with SMART.new_session() as session:
        fetch = crud.FetchLifecycle(session)
        rolling_status_list = fetch.get_all_rolling_status()

    return jsonify(rolling_status_list), 200


@application.route("/lifecycle/ignition", methods=["GET"])
def lifecycle_get_ignition_status():
    """
    Lifecycle Ignition Update
    Get the update status of all Ignition reports
    ---
    tags:
      - lifecycle
    responses:
      200:
        description: Ignition Update status
        schema:
            type: list
    """
    with SMART.new_session() as session:
        fetch = crud.FetchLifecycle(session)
        updated_status_list = fetch.get_all_updated_status()

    return jsonify(updated_status_list), 200


@application.route("/lifecycle/coreos-install", methods=["GET"])
def lifecycle_get_coreos_install_status():
    """
    Lifecycle CoreOS Install
    Get all the CoreOS Install status
    ---
    tags:
      - lifecycle
    responses:
      200:
        description: CoreOS Install status list
        schema:
            type: list
    """
    with SMART.new_session() as session:
        fetch = crud.FetchLifecycle(session)
        install_status_list = fetch.get_all_coreos_install_status()

    return jsonify(install_status_list)


@application.route("/lifecycle/coreos-install/<string:status>/<string:request_raw_query>", methods=["POST"])
def report_lifecycle_coreos_install(status, request_raw_query):
    """
    Lifecycle CoreOS Install
    Report the status of a CoreOS install by MAC
    ---
    tags:
      - lifecycle
    responses:
      200:
        description: CoreOS Install report
        schema:
            type: dict
    """
    app.logger.info("%s %s" % (request.method, request.url))
    if status.lower() == "success":
        success = True
    elif status.lower() == "fail":
        success = False
    else:
        app.logger.error("%s %s" % (request.method, request.url))
        return "success or fail != %s" % status.lower(), 403

    @smartdb.cockroach_transaction
    def op(caller=request.url_rule):
        with SMART.new_session() as session:
            inject = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
            inject.refresh_lifecycle_coreos_install(success)

    op(caller=request.url_rule)
    repositories.machine_state.update(
        mac=tools.get_mac_from_raw_query(request_raw_query),
        state=MachineStates.installation_succeed if success else MachineStates.installation_failed)
    return jsonify({"success": success, "request_raw_query": request_raw_query}), 200


@application.route('/', methods=['GET'])
def api_mapper():
    """
    Map the API
    List all the available routes
    ---
    tags:
      - ops
    responses:
      200:
        description: Routes
        schema:
            type: list
    """
    rules = [k.rule for k in application.url_map.iter_rules()]
    rules = list(set(rules))
    rules.sort()
    return jsonify(rules)


@application.route('/healthz', methods=['GET'])
def healthz():
    """
    Health
    Get the status of the application
    ---
    tags:
      - ops
    responses:
      200:
        description: Components status
        schema:
            type: dict
    """
    data = ops.healthz(application, SMART, request)
    res = jsonify(data), 503 if data["global"] is False else 200
    resp = make_response(res)
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp


@application.route('/discovery', methods=['POST'])
def record_discovery_data():
    """
    Discovery
    Report the current facts of a machine
    ---
    tags:
      - discovery
    responses:
      200:
        description: Number of machines and if the machine is new
        schema:
            type: dict
    """
    app.logger.info("%s %s" % (request.method, request.url))
    err = jsonify({u'boot-info': {}, u'lldp': {}, u'interfaces': [], u"disks": []}), 406
    try:
        discovery_data = json.loads(request.get_data())
    except (KeyError, TypeError, ValueError):
        logger.error("fail to parse discovery data: %s" % request.get_data())
        return err

    try:
        new = repositories.discovery.upsert(discovery_data)
        repositories.machine_state.update(discovery_data["boot-info"]["mac"], MachineStates.discovery)
        CACHE.delete(request.path)
        return jsonify({"new-discovery": new}), 200
    except TypeError as e:
        logger.error("fail to store discovery data: %s -> %s" % (request.get_data(), e))
        return err


@application.route('/discovery', methods=['GET'])
def get_discovery_data():
    """
    Discovery
    List
    ---
    tags:
      - discovery
    responses:
      200:
        description: Discovery data
        schema:
            type: list
    """
    all_data = CACHE.get(request.path)
    if not all_data:
        all_data = repositories.discovery.fetch_all_discovery()
        CACHE.set(request.path, all_data, timeout=30)
    return jsonify(all_data)


@application.route('/scheduler', methods=['GET'])
def scheduler_get():
    """
    Scheduler
    List all the running schedules
    ---
    tags:
      - scheduler
    responses:
      200:
        description: Current schedules
        schema:
            type: list
    """
    all_data = CACHE.get(request.path)
    if all_data is None:
        all_data = repositories.machine_schedule.get_all_schedules()
        CACHE.set(request.path, all_data, timeout=10)

    return jsonify(all_data)


@application.route('/scheduler/<string:role>', methods=['GET'])
def get_schedule_by_role(role):
    """
    Scheduler
    List all the running schedules
    ---
    tags:
      - scheduler
    parameters:
      - name: role
        in: path
        description: name of the role
        required: true
        type: string
    responses:
      200:
        description: Current schedules for a given role
        schema:
            type: list
    """
    multi = role.split("&")
    data = repositories.machine_schedule.get_machines_by_roles(*multi)
    return jsonify(data)


@application.route('/scheduler/available', methods=['GET'])
def get_available_machine():
    """
    Scheduler
    List all the machine without schedule
    ---
    tags:
      - scheduler
    responses:
      200:
        description: Current machine available for a schedule
        schema:
            type: list
    """
    data = repositories.machine_schedule.get_available_machines()
    return jsonify(data)


@application.route('/scheduler/ip-list/<string:role>', methods=['GET'])
def get_schedule_role_ip_list(role):
    """
    Scheduler
    List all the IP addresses of a given schedules role
    ---
    tags:
      - scheduler
    parameters:
      - name: role
        in: path
        description: name of the role
        required: true
        type: string
    responses:
      200:
        description: Current IP address of schedules for a given role
        schema:
            type: list
    """
    ip_list_role = repositories.machine_schedule.get_role_ip_list(role)

    return jsonify(ip_list_role)


@application.route('/scheduler', methods=['POST'])
def scheduler_post():
    """
    Scheduler
    Affect a schedule to a machine
    ---
    tags:
      - scheduler
    responses:
      406:
        description: Incorrect body content
        schema:
            type: dict
      200:
        description: The body sent
        schema:
            type: dict
    """
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

    @smartdb.cockroach_transaction
    def op(caller=request.url_rule):
        with SMART.new_session() as session:
            inject = crud.InjectSchedule(session, data=req)
            inject.apply_roles()
            inject.commit()

    op(caller=request.url_rule)
    CACHE.delete(request.path)
    return jsonify(req)


@application.route('/backup/db', methods=['POST'])
def backup_database():
    """
    Backup
    Backup the database if it's SQLite
    ---
    tags:
      - ops
    responses:
      200:
        description: Backup report
        schema:
            type: dict
      404:
        description: If the database is not SQLite
        schema:
            type: dict
    """
    if "sqlite://" in EC.db_uri:
        return ops.backup_sqlite(cache=CACHE, application=application)
    return jsonify({"NotImplementedError": "%s" % EC.db_uri}), 404


@application.route('/backup/export', methods=['GET'])
def backup_as_export():
    """
    Backup by exporting a playbook of what discovery client and schedulers sent to the API
    Allows to just run each entry against the enjoliver API
    Note: it doesnt export the LLDP data eventually stored in the DB
    ---
    tags:
      - ops
    responses:
      200:
        description: Backup playbook
        schema:
            type: list
    """
    with SMART.new_session() as session:
        exporter = crud.BackupExport(session)
        playbook = exporter.get_playbook()

    return jsonify(playbook), 200


@application.route('/ignition/version', methods=['GET'])
def get_ignition_versions():
    """
    Ignition version
    List the current ignition behind matchbox
    ---
    tags:
      - matchbox
    responses:
      200:
        description: Ignition version
        schema:
            type: list
    """
    return jsonify(CACHE.get("ignition-version"))


@application.route('/ignition/version/<string:filename>', methods=['POST'])
def report_ignition_version(filename):
    """
    Ignition version
    Report the current ignition behind matchbox
    ---
    tags:
      - matchbox
    responses:
      200:
        description: Status of the recorded entry
        schema:
            type: dict
    """
    versions = CACHE.get("ignition-version")
    if not versions:
        versions = dict()

    new_entry = False if filename in versions.keys() else True
    data = json.loads(request.data)
    versions.update({filename: data[filename]})
    CACHE.set("ignition-version", versions, timeout=0)
    return jsonify({"new": new_entry, "total": len(versions)})


@application.route('/boot.ipxe', methods=['GET'])
@application.route('/boot.ipxe.0', methods=['GET'])
def boot_ipxe():
    """
    iPXE
    ---
    tags:
      - matchbox
    responses:
      200:
        description: iPXE boot script to chain load on /ipxe
        schema:
            type: string
    """
    app.logger.info("%s %s" % (request.method, request.url))
    try:
        flask_uri = application.config["API_URI"]
        if flask_uri is None:
            raise AttributeError("API_URI is None")
        app.logger.debug("%s" % flask_uri)

    except Exception as e:
        flask_uri = application.config["MATCHBOX_URI"]
        app.logger.error("<%s %s>" % (e, type(e)))
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
    return Response(response, status=200, mimetype="text/plain")


@application.route("/sync-notify", methods=["POST"])
def sync_notify():
    """
    Sync process notify POST to this route to tell everything is synced for matchbox
    ---
    tags:
      - matchbox
    responses:
      200:
        description: Notify received
        schema:
            type: dict
    """
    ts = time.time()
    CACHE.set("sync-notify", ts, timeout=EC.sync_notify_ttl)
    return jsonify({"ts": ts, "ttl": EC.sync_notify_ttl}), 200


@application.route("/sync-notify", methods=["GET"])
def sync_notify_status():
    """
    Sync process notify POST to this route to tell everything is synced for matchbox
    ---
    tags:
      - matchbox
    responses:
      200:
        description: Notify received
        schema:
            type: dict
    """
    sync = CACHE.get("sync-notify")
    if sync:
        return jsonify({"sync-notify": sync}), 200

    app.logger.warning("sync-notify is None")
    return jsonify({"sync-notify": False}), 503


@application.route("/ignition", methods=["GET"])
@application.route("/ignition-pxe", methods=["GET"])
def ignition():
    """
    Ignition
    ---
    tags:
      - matchbox
    responses:
      200:
        description: Ignition configuration
        schema:
            type: dict
      403:
        description: Matchbox unavailable
        schema:
            type: text/plain
      503:
        description: Matchbox is out of sync
        schema:
            type: text/plain
    """
    cache_key = "sync-notify"
    last_sync_ts = CACHE.get(cache_key)
    app.logger.debug("cacheKey: %s is set with value %s" % (cache_key, last_sync_ts))

    # we ignore the sync status if we arrived from /ignition-pxe because it's a discovery PXE boot
    if last_sync_ts is None and request.path != "/ignition-pxe":
        app.logger.error("matchbox state is out of sync: cacheKey: %s is None" % cache_key)
        return Response("matchbox is out of sync", status=503, mimetype="text/plain")

    matchbox_uri = application.config.get("MATCHBOX_URI")
    if matchbox_uri:
        try:
            # remove the -pxe from the path because matchbox only serve /ignition
            path = request.full_path.replace("/ignition-pxe?", "/ignition?")
            matchbox_resp = requests.get("%s%s" % (matchbox_uri, path))
            resp = matchbox_resp.content
            matchbox_resp.close()
            return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")
        except requests.RequestException as e:
            app.logger.error("fail to query matchbox ignition %s" % e)
            return Response("matchbox doesn't respond", status=502, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@application.route("/metadata", methods=["GET"])
def metadata():
    """
    Metadata
    ---
    tags:
      - matchbox
    responses:
      200:
        description: Metadata of the current group/profile
        schema:
            type: string
    """
    matchbox_uri = application.config.get("MATCHBOX_URI")
    if matchbox_uri:
        matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
        resp = matchbox_resp.content
        matchbox_resp.close()
        return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@application.route('/install-authorization/<string:request_raw_query>')
def require_install_authorization(request_raw_query):
    """
    Install Authorization
    Temporize the installation to avoid burst of downloads / extract in memory
    ---
    tags:
      - ops
    responses:
      200:
        description: Granted to install
        schema:
            type: string
      403:
        description: Locked
        schema:
            type: string
    """
    app.logger.info("%s %s %s" % (request.method, request.remote_addr, request.url))
    if EC.coreos_install_lock_seconds > 0:
        lock = CACHE.get("lock-install")
        if lock is not None:
            app.logger.warning("Locked by %s" % lock)
            repositories.machine_state.update(tools.get_mac_from_raw_query(request_raw_query),
                                              MachineStates.os_installation_denied)
            return Response(response="Locked by %s" % lock, status=403)
        CACHE.set("lock-install", request_raw_query, timeout=EC.coreos_install_lock_seconds)
        app.logger.info("Granted to %s" % request_raw_query)

    repositories.machine_state.update(tools.get_mac_from_raw_query(request_raw_query),
                                      MachineStates.os_installation_granted)
    return Response(response="Granted", status=200)


@application.route('/assets', defaults={'path': ''})
@application.route('/assets/<path:path>')
def assets(path):
    """
    Assets server
    Serve the assets
    ---
    tags:
      - matchbox
    responses:
      200:
        description: Content of the asset
      404:
        description: Not valid
        schema:
            type: string
    """
    app.logger.info("%s %s" % (request.method, request.url))
    matchbox_uri = application.config.get("MATCHBOX_URI")
    if matchbox_uri:
        url = "%s/assets/%s" % (matchbox_uri, path)
        matchbox_resp = requests.get(url)
        resp = matchbox_resp.content
        matchbox_resp.close()
        return Response(response=resp, mimetype="application/octet-stream")

    return Response("matchbox=%s" % matchbox_uri, status=404, mimetype="text/plain")


@application.route('/ipxe', methods=['GET'])
def ipxe():
    """
    iPXE
    ---
    tags:
      - matchbox
    responses:
      200:
        description: iPXE script
        schema:
            type: string
      404:
        description: Not valid
        schema:
            type: string
    """
    app.logger.info("%s %s" % (request.method, request.url))
    try:
        matchbox_resp = requests.get(
            "%s%s" % (
                app.config["MATCHBOX_URI"],
                request.full_path))
        matchbox_resp.close()
        response = matchbox_resp.content.decode()

        mac = request.args.get("mac")
        if mac:
            repositories.machine_state.update(mac.replace("-", ":"), MachineStates.booting)

        return Response(response, status=200, mimetype="text/plain")

    except requests.exceptions.ConnectionError:
        app.logger.warning("404 for /ipxe")
        return "404", 404


@application.errorhandler(404)
def page_not_found(error):
    return Response("404", status=404, mimetype="text/plain")


@application.route('/ui', methods=['GET'])
def user_interface():
    return render_template("index.html")


@application.route('/ui/view/machine', methods=['GET'])
def user_view_machine():
    res = jsonify(repositories.user_interface.get_machines_overview())
    resp = make_response(res)
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp


@application.route('/ui/view/states', methods=['GET'])
def user_view_machine_statuses():
    data_since_last_min = request.args.get('data_since_last_min') if request.args.get('data_since_last_min') else 30
    res = jsonify(repositories.machine_state.fetch(finished_in_less_than_min=int(data_since_last_min)))
    resp = make_response(res)
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp


if __name__ == "__main__":
    application.run(debug=True)
