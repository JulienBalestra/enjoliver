import os
import socket
import urllib2

import requests
from flask import Flask, request, json, jsonify, render_template, Response
from sqlalchemy import create_engine

import crud
import logger
import model
import ops
from configs import EnjoliverConfig

ec = EnjoliverConfig(importer=__file__)

from werkzeug.contrib.cache import FileSystemCache

cache = FileSystemCache(ec.werkzeug_fs_cache_dir)

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


@application.route("/shutdown", methods=["POST"])
def shutdown():
    return ops.shutdown(ec)


@application.route("/configs", methods=["GET"])
def configs():
    return jsonify(ec.__dict__)


@application.route("/lifecycle/ignition/<string:request_raw_query>", methods=["POST"])
def lifecycle_post_ignition(request_raw_query):
    try:
        machine_ignition = json.loads(request.get_data())
    except ValueError:
        LOGGER.error("%s have incorrect content" % request.path)
        return "FlaskValueError", 406
    req = requests.get("%s/ignition?%s" % (ec.matchbox_uri, request_raw_query))
    try:
        matchbox_ignition = json.loads(req.content)
        req.close()
    except ValueError:
        LOGGER.error("%s have incorrect matchbox return" % request.path)
        return "MatchboxValueError", 406
    i = crud.InjectLifecycle(engine=engine, request_raw_query=request_raw_query)
    if json.dumps(machine_ignition, sort_keys=True) == json.dumps(matchbox_ignition, sort_keys=True):
        i.refresh_lifecycle_ignition(True)
        r = "Up-to-date", 200
    else:
        i.refresh_lifecycle_ignition(False)
        r = "Outdated", 210
    return r


@application.route("/lifecycle/ignition", methods=["GET"])
def lifecycle_get_ignition_status():
    q = crud.FetchLifecycle(engine)
    d = q.get_all_updated_status()
    q.close()
    return jsonify(d)


@application.route("/lifecycle/coreos-install", methods=["GET"])
def lifecycle_get_coreos_install_status():
    q = crud.FetchLifecycle(engine)
    d = q.get_all_coreos_install_status()
    q.close()
    return jsonify(d)


@application.route("/lifecycle/coreos-install/<string:request_raw_query>/success", methods=["POST"])
def lifecycle_post_coreos_install_success(request_raw_query):
    i = crud.InjectLifecycle(engine=engine, request_raw_query=request_raw_query)
    i.refresh_lifecycle_coreos_install(True)
    return "", 200


@application.route("/lifecycle/coreos-install/<string:request_raw_query>/fail", methods=["POST"])
def lifecycle_post_coreos_install_fail(request_raw_query):
    i = crud.InjectLifecycle(engine=engine, request_raw_query=request_raw_query)
    i.refresh_lifecycle_coreos_install(False)
    return "", 200


@application.route('/', methods=['GET'])
def root():
    """
    Map the API
    :return: available routes
    """
    r = [k.rule for k in application.url_map.iter_rules()]
    r = list(set(r))
    return jsonify(r)


@application.route('/healthz', methods=['GET'])
def healthz():
    return jsonify(ops.healthz(application, engine, request))


@application.route('/discovery', methods=['POST'])
def discovery():
    try:
        r = json.loads(request.get_data())
        i = crud.InjectDiscovery(engine=engine,
                                 ignition_journal=ignition_journal,
                                 discovery=r)
        new = i.commit_and_close()
        cache.delete(request.path)
        return jsonify({"total_elt": new[0], "new": new[1]})

    except (KeyError, TypeError, ValueError):
        return jsonify(
            {
                u'boot-info': {},
                u'lldp': {},
                u'interfaces': []
            }), 406


@application.route('/discovery', methods=['GET'])
def discovery_get():
    all_data = cache.get(request.path)
    if all_data is None:
        fetch = crud.FetchDiscovery(
            engine=engine,
            ignition_journal=ignition_journal
        )
        try:
            all_data = fetch.get_all()
            cache.set(request.path, all_data, timeout=30)
        finally:
            fetch.close()

    return jsonify(all_data)


@application.route('/scheduler', methods=['GET'])
def scheduler_get():
    all_data = cache.get(request.path)
    if all_data is None:
        fetch = crud.FetchSchedule(
            engine=engine,
        )
        try:
            all_data = fetch.get_schedules()
            fetch.close()
            cache.set(request.path, all_data, timeout=30)
        finally:
            fetch.close()

    return jsonify(all_data)


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
def scheduler_post():
    try:
        r = json.loads(request.get_data())
        inject = crud.InjectSchedule(
            engine=engine,
            data=r)
        try:
            inject.apply_roles()
        finally:
            inject.commit_and_close()
    except ValueError:
        return jsonify(
            {
                u"roles": model.ScheduleRoles.roles,
                u'selector': {
                    u"mac": ""
                }
            }), 406

    cache.delete(request.path)
    return jsonify(r)


@application.route('/backup/db', methods=['POST'])
def backup_database():
    return ops.backup_sqlite(cache=cache, application=application)


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
    """
    TODO This will change to use VueJS and avoid multiple queries
    :return:
    """

    key = "discovery"
    all_data = cache.get(key)
    if all_data is None:
        fetch = crud.FetchDiscovery(
            engine=engine,
            ignition_journal=ignition_journal
        )
        all_data = fetch.get_all()
        cache.set(key, all_data, timeout=30)

    res = [["Created", "cidr-boot", "mac-boot", "fqdn", "Roles", "Installed", "Up-to-date"]]
    for i in all_data:
        sub_list = list()
        sub_list.append(i["boot-info"]["created-date"])
        for j in i["interfaces"]:
            if j["as_boot"]:
                sub_list.append(j["cidrv4"])
                sub_list.append(j["mac"])
                ip = j["cidrv4"].split("/")[0]
                cache_key = "/ui/view/machine?fqdn-%s" % ip
                fqdn = cache.get(cache_key)
                if not fqdn:
                    try:
                        fqdn = socket.gethostbyaddr(ip)[0]
                        cache.set(cache_key, fqdn, timeout=60 * 10)
                    except socket.herror:
                        fqdn = "unknown"
                sub_list.append(fqdn)
                try:
                    s = crud.FetchSchedule(engine)
                    roles = s.get_roles_by_mac_selector(j["mac"])
                finally:
                    s.close()
                sub_list.append(roles if roles else "none")
                lf = crud.FetchLifecycle(engine)
                sub_list.append(lf.get_coreos_install_status(j["mac"]))
                sub_list.append(lf.get_ignition_uptodate_status(j["mac"]))
                lf.close()

        res.append(sub_list)

    return jsonify(res)


if __name__ == "__main__":
    app.logger.setLevel("DEBUG")
    application.run(debug=True)
