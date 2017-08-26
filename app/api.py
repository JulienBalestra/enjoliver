import json as std_json
import os

import requests
from flasgger import Swagger
from flask import Flask, request, json, jsonify, render_template, Response
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from prometheus_client import multiprocess
from werkzeug.contrib.cache import FileSystemCache

import crud
import logger
import model
import monitoring
import ops
import smartdb
from configs import EnjoliverConfig
from smartdb import SmartDatabaseClient

EC = EnjoliverConfig(importer=__file__)

CACHE = FileSystemCache(EC.werkzeug_fs_cache_dir)

LOGGER = logger.get_logger(__file__)

APP = APPLICATION = Flask(__name__)
jinja_options = APP.jinja_options.copy()
jinja_options.update(dict(
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='%%',
    variable_end_string='%%',
    comment_start_string='<#',
    comment_end_string='#>'
))
APP.jinja_options = jinja_options

Swagger(APP)

APPLICATION.config["MATCHBOX_URI"] = EC.matchbox_uri
APPLICATION.config["API_URI"] = EC.api_uri

APPLICATION.config["MATCHBOX_URLS"] = EC.matchbox_urls

APPLICATION.config["DB_PATH"] = EC.db_path
APPLICATION.config["DB_URI"] = EC.db_uri

ignition_journal = APPLICATION.config["IGNITION_JOURNAL_DIR"] = EC.ignition_journal_dir

APPLICATION.config["BACKUP_BUCKET_NAME"] = EC.backup_bucket_name
APPLICATION.config["BACKUP_BUCKET_DIRECTORY"] = EC.backup_bucket_directory
APPLICATION.config["BACKUP_LOCK_KEY"] = EC.backup_lock_key

SMART = SmartDatabaseClient

if __name__ == '__main__' or "gunicorn" in os.getenv("SERVER_SOFTWARE", ""):
    SMART = SmartDatabaseClient(APPLICATION.config["DB_URI"])

    if "gunicorn" in os.getenv("SERVER_SOFTWARE", "") and os.getenv('prometheus_multiproc_dir'):
        @APPLICATION.route("/metrics", methods=["GET"])
        def collect():
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            data = generate_latest(registry)
            return Response(data, mimetype=CONTENT_TYPE_LATEST)


def before_request():
    try:
        # don't monitor /metrics
        if request.url_rule.rule != "/metrics":
            monitoring.FlaskMonitoringComponents(request.url_rule.endpoint).before()
    except AttributeError:
        # 404
        pass
    except Exception as e:
        LOGGER.error("monitor request: type(%s) %s: %s" % (type(e), e, request.path))


def after_request(response):
    try:
        # don't monitor /metrics
        if request.url_rule.rule != "/metrics":
            monitoring.FlaskMonitoringComponents(request.url_rule.endpoint).after(response)
    except AttributeError:
        # 404
        pass
    except Exception as e:
        LOGGER.error("monitor request: type(%s) %s: %s" % (type(e), e, request.path))
    finally:
        return response


APP.before_request(before_request)
APP.after_request(after_request)


@APPLICATION.route("/shutdown", methods=["POST"])
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


@APPLICATION.route("/configs", methods=["GET"])
@APPLICATION.route("/config", methods=["GET"])
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


@APPLICATION.route("/lifecycle/ignition/<string:request_raw_query>", methods=["POST"])
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
        LOGGER.error("%s have incorrect content" % request.path)
        return jsonify({"message": "FlaskValueError"}), 406
    req = requests.get("%s/ignition?%s" % (EC.matchbox_uri, request_raw_query))
    try:
        matchbox_ignition = json.loads(req.content)
        req.close()
    except ValueError:
        LOGGER.error("%s have incorrect matchbox return" % request.path)
        return jsonify({"message": "MatchboxValueError"}), 406

    @smartdb.cockroach_transaction
    def op():
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

    return op()


@APPLICATION.route("/lifecycle/rolling/<string:request_raw_query>", methods=["GET"])
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
            mac = crud.InjectLifecycle.get_mac_from_raw_query(request_raw_query)
        except AttributeError as e:
            return jsonify({"enable": None, "request_raw_query": "%s:%s" % (request_raw_query, e)}), 403

        allow, strategy = life.get_rolling_status(mac)

        if allow is True:
            return jsonify({"enable": True, "request_raw_query": request_raw_query, "strategy": strategy}), 200
        elif allow is False:
            return jsonify({"enable": False, "request_raw_query": request_raw_query, "strategy": strategy}), 403

    return jsonify({"enable": False, "request_raw_query": request_raw_query, "strategy": None}), 401


@APPLICATION.route("/lifecycle/rolling/<string:request_raw_query>", methods=["POST"])
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
    LOGGER.info("%s %s" % (request.method, request.url))
    try:
        strategy = json.loads(request.get_data())["strategy"]
        LOGGER.info("%s %s rolling strategy: setting to %s" % (request.method, request.url, strategy))
    except (KeyError, std_json.decoder.JSONDecodeError):
        LOGGER.info("%s %s rolling strategy: setting default to kexec" % (request.method, request.url))
        strategy = "kexec"

    @smartdb.cockroach_transaction
    def op():
        with SMART.new_session() as session:
            try:
                life = crud.InjectLifecycle(session, request_raw_query)
                life.apply_lifecycle_rolling(True, strategy)
                return jsonify({"enable": True, "request_raw_query": request_raw_query, "strategy": strategy}), 200
            except AttributeError:
                return jsonify({"enable": None, "request_raw_query": request_raw_query, "strategy": strategy}), 401

    return op()


@APPLICATION.route("/lifecycle/rolling/<string:request_raw_query>", methods=["DELETE"])
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
    LOGGER.info("%s %s" % (request.method, request.url))

    @smartdb.cockroach_transaction
    def op():
        with SMART.new_session() as session:
            life = crud.InjectLifecycle(session, request_raw_query)
            life.apply_lifecycle_rolling(False, None)
            return jsonify({"enable": False, "request_raw_query": request_raw_query}), 200

    return op()


@APPLICATION.route("/lifecycle/rolling", methods=["GET"])
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


@APPLICATION.route("/lifecycle/ignition", methods=["GET"])
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


@APPLICATION.route("/lifecycle/coreos-install", methods=["GET"])
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


@APPLICATION.route("/lifecycle/coreos-install/<string:status>/<string:request_raw_query>", methods=["POST"])
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
    LOGGER.info("%s %s" % (request.method, request.url))
    if status.lower() == "success":
        success = True
    elif status.lower() == "fail":
        success = False
    else:
        LOGGER.error("%s %s" % (request.method, request.url))
        return "success or fail != %s" % status.lower(), 403

    @smartdb.cockroach_transaction
    def op():
        with SMART.new_session() as session:
            inject = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
            inject.refresh_lifecycle_coreos_install(success)

    op()
    return jsonify({"success": success, "request_raw_query": request_raw_query}), 200


@APPLICATION.route('/', methods=['GET'])
def root():
    """
    Map the API
    List all the avaiable routes
    ---
    tags:
      - ops
    responses:
      200:
        description: Routes
        schema:
            type: list
    """
    rules = [k.rule for k in APPLICATION.url_map.iter_rules()]
    rules = list(set(rules))
    rules.sort()
    return jsonify(rules)


@APPLICATION.route('/healthz', methods=['GET'])
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
    resp = ops.healthz(APPLICATION, SMART, request)
    return jsonify(resp), 503 if resp["global"] is False else 200


@APPLICATION.route('/discovery', methods=['POST'])
def discovery():
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
    LOGGER.info("%s %s" % (request.method, request.url))
    err = jsonify({u'boot-info': {}, u'lldp': {}, u'interfaces': [], u"disks": []}), 406
    try:
        req = json.loads(request.get_data())
    except (KeyError, TypeError, ValueError):
        return err

    @smartdb.cockroach_transaction
    def op():
        with SMART.new_session() as session:
            inject = crud.InjectDiscovery(
                session,
                ignition_journal=ignition_journal,
                discovery=req)
            new = inject.commit()
            CACHE.delete(request.path)
            return jsonify({"total_elt": new[0], "new": new[1]})

    try:
        return op()
    except TypeError:
        return err


@APPLICATION.route('/discovery', methods=['GET'])
def discovery_get():
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
    if all_data is None:
        with SMART.new_session() as session:
            fetch = crud.FetchDiscovery(session, ignition_journal=ignition_journal)
            all_data = fetch.get_all()
            CACHE.set(request.path, all_data, timeout=30)
    return jsonify(all_data)


@APPLICATION.route('/scheduler', methods=['GET'])
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
        with SMART.new_session() as session:
            fetch = crud.FetchSchedule(session)
            all_data = fetch.get_schedules()
            CACHE.set(request.path, all_data, timeout=30)

    return jsonify(all_data)


@APPLICATION.route('/scheduler/<string:role>', methods=['GET'])
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
    with SMART.new_session() as session:
        fetch = crud.FetchSchedule(session)
        multi = role.split("&")
        data = fetch.get_machines_by_roles(*multi)

    return jsonify(data)


@APPLICATION.route('/scheduler/available', methods=['GET'])
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
    with SMART.new_session() as session:
        fetch = crud.FetchSchedule(session)
        data = fetch.get_available_machines()

    return jsonify(data)


@APPLICATION.route('/scheduler/ip-list/<string:role>', methods=['GET'])
def get_schedule_role_ip_list(role):
    """
    Scheduler
    List all the IP addresse of a given schedules role
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
    with SMART.new_session() as session:
        fetch = crud.FetchSchedule(session)
        ip_list_role = fetch.get_role_ip_list(role)

    return jsonify(ip_list_role)


@APPLICATION.route('/scheduler', methods=['POST'])
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
    def op():
        with SMART.new_session() as session:
            inject = crud.InjectSchedule(session, data=req)
            inject.apply_roles()
            inject.commit()

    op()
    CACHE.delete(request.path)
    return jsonify(req)


@APPLICATION.route('/backup/db', methods=['POST'])
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
        return ops.backup_sqlite(cache=CACHE, application=APPLICATION)
    return jsonify({"NotImplementedError": "%s" % EC.db_uri}), 404


@APPLICATION.route('/backup/export', methods=['GET'])
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


@APPLICATION.route('/discovery/interfaces', methods=['GET'])
def discovery_interfaces():
    """
    Discovery
    List only the interfaces
    ---
    tags:
      - discovery
    responses:
      200:
        description: Discovery interfaces
        schema:
            type: list
    """
    with SMART.new_session() as session:
        fetch = crud.FetchDiscovery(session, ignition_journal=ignition_journal)
        interfaces = fetch.get_all_interfaces()

    return jsonify(interfaces)


@APPLICATION.route('/ignition/version', methods=['GET'])
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


@APPLICATION.route('/ignition/version/<string:filename>', methods=['POST'])
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

    data = json.loads(request.data)
    new_entry = True
    if filename in versions.keys():
        new_entry = False
    versions.update({filename: data[filename]})
    CACHE.set("ignition-version", versions, timeout=0)
    return jsonify({"new": new_entry, "total": len(versions)})


@APPLICATION.route('/discovery/ignition-journal/<string:uuid>/<string:boot_id>', methods=['GET'])
def discovery_ignition_journal_by_boot_id(uuid, boot_id):
    """
    Discovery
    Get the Ignition journal
    ---
    tags:
      - discovery
    parameters:
      - name: uuid
        in: path
        description: uuid of the machine
        required: true
        type: string
      - name: boot_id
        in: path
        description: boot-id of the machine
        required: true
        type: string
    responses:
      200:
        description: Lines of the journal
        schema:
            type: list
    """
    with SMART.new_session() as session:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal(uuid, boot_id=boot_id)

    return jsonify(lines)


@APPLICATION.route('/discovery/ignition-journal/<string:uuid>', methods=['GET'])
def discovery_ignition_journal_by_uuid(uuid):
    """
    Discovery
    Get the Ignition journal
    ---
    tags:
      - discovery
    parameters:
      - name: uuid
        in: path
        description: uuid of the machine
        required: true
        type: string
    responses:
      200:
        description: Lines of the journal
        schema:
            type: list
    """
    with SMART.new_session() as session:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal(uuid)

    return jsonify(lines)


@APPLICATION.route('/discovery/ignition-journal', methods=['GET'])
def discovery_ignition_journal_summary():
    """
    Discovery
    Get the available Ignition journal
    ---
    tags:
      - discovery
    responses:
      200:
        description: Lines available journals
        schema:
            type: list
    """
    with SMART.new_session() as session:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal_summary()

    return jsonify(lines)


@APPLICATION.route('/boot.ipxe', methods=['GET'])
@APPLICATION.route('/boot.ipxe.0', methods=['GET'])
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
    """
    matchbox_uri = APPLICATION.config.get("MATCHBOX_URI")
    if matchbox_uri:
        matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
        resp = matchbox_resp.content
        matchbox_resp.close()
        return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@APPLICATION.route("/metadata", methods=["GET"])
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
    matchbox_uri = APPLICATION.config.get("MATCHBOX_URI")
    if matchbox_uri:
        matchbox_resp = requests.get("%s%s" % (matchbox_uri, request.full_path))
        resp = matchbox_resp.content
        matchbox_resp.close()
        return Response(resp, status=matchbox_resp.status_code, mimetype="text/plain")

    return Response("matchbox=%s" % matchbox_uri, status=403, mimetype="text/plain")


@APPLICATION.route('/install-authorization/<string:request_raw_query>')
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
    LOGGER.info("%s %s %s" % (request.method, request.remote_addr, request.url))
    if EC.coreos_install_lock_seconds > 0:
        lock = CACHE.get("lock-install")
        if lock is not None:
            LOGGER.warning("Locked by %s" % lock)
            return Response(response="Locked by %s" % lock, status=403)
        CACHE.set("lock-install", request_raw_query, timeout=EC.coreos_install_lock_seconds)
        LOGGER.info("Granted to %s" % request_raw_query)
    return Response(response="Granted", status=200)


@APPLICATION.route('/assets', defaults={'path': ''})
@APPLICATION.route('/assets/<path:path>')
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


@APPLICATION.errorhandler(404)
def page_not_found(error):
    return Response("404", status=404, mimetype="text/plain")


@APPLICATION.route('/ui', methods=['GET'])
def user_interface():
    return render_template("index.html")


@APPLICATION.route('/ui/view/machine', methods=['GET'])
def user_view_machine():
    with SMART.new_session() as session:
        view = crud.FetchView(session)
        res = view.get_machines()

    return jsonify(res)


if __name__ == "__main__":
    APP.logger.setLevel("DEBUG")
    APPLICATION.run(debug=True)
