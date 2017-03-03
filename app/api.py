import requests
from flask import Flask, request, json, jsonify, render_template, Response

import crud
import logger
import model
import ops
from configs import EnjoliverConfig
from smartdb import SmartClient

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

application.config["SMART_CLIENT"] = SmartClient(application.config["DB_URI"])
smart = application.config["SMART_CLIENT"]


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

    conn, session = smart.create_conn_with_session()
    try:
        i = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
        if json.dumps(machine_ignition, sort_keys=True) == json.dumps(matchbox_ignition, sort_keys=True):
            i.refresh_lifecycle_ignition(True)
            r = "Up-to-date", 200
        else:
            i.refresh_lifecycle_ignition(False)
            r = "Outdated", 210
    finally:
        session.close()
        conn.close()
    return r


@application.route("/lifecycle/rolling/<string:request_raw_query>", methods=["GET"])
def lifecycle_rolling_get(request_raw_query):
    conn, session = smart.create_conn_with_session()
    try:
        life = crud.FetchLifecycle(session)
        mac = crud.InjectLifecycle.get_mac_from_raw_query(request_raw_query)
        d = life.get_rolling_status(mac)

        if d is True:
            return "Enabled %s" % mac, 200
        elif d is False:
            return "Disable %s" % mac, 403
    finally:
        session.close()
        conn.close()

    return "ForeignDisabled %s" % mac, 401


@application.route("/lifecycle/rolling/<string:request_raw_query>", methods=["POST"])
def lifecycle_rolling_post(request_raw_query):
    conn, session = smart.create_conn_with_session()
    try:
        life = crud.InjectLifecycle(session, request_raw_query)
        life.apply_lifecycle_rolling(True)
        d = "Enabled %s" % life.mac, 200
    except AttributeError:
        d = "Unknown in db %s" % request_raw_query, 401
    finally:
        session.close()
        conn.close()
    return d


@application.route("/lifecycle/rolling/<string:request_raw_query>", methods=["DELETE"])
def lifecycle_rolling_delete(request_raw_query):
    conn, session = smart.create_conn_with_session()
    try:
        life = crud.InjectLifecycle(session, request_raw_query)
        life.apply_lifecycle_rolling(False)
        d = "Disabled %s" % life.mac, 200
    finally:
        session.close()
        conn.close()
    return d


@application.route("/lifecycle/rolling", methods=["GET"])
def lifecycle_rolling_all():
    conn, session = smart.create_conn_with_session()
    try:
        life = crud.FetchLifecycle(session)
        d = life.get_all_rolling_status()
    finally:
        session.close()
        conn.close()
    return jsonify(d)


@application.route("/lifecycle/ignition", methods=["GET"])
def lifecycle_get_ignition_status():
    conn, session = smart.create_conn_with_session()
    try:
        q = crud.FetchLifecycle(session)
        d = q.get_all_updated_status()
    finally:
        session.close()
        conn.close()
    return jsonify(d)


@application.route("/lifecycle/coreos-install", methods=["GET"])
def lifecycle_get_coreos_install_status():
    conn, session = smart.create_conn_with_session()
    try:
        q = crud.FetchLifecycle(session)
        d = q.get_all_coreos_install_status()
    finally:
        session.close()
        conn.close()
    return jsonify(d)


@application.route("/lifecycle/coreos-install/success/<string:request_raw_query>", methods=["POST"])
def lifecycle_post_coreos_install_success(request_raw_query):
    conn, session = smart.create_conn_with_session()
    try:
        i = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
        i.refresh_lifecycle_coreos_install(True)
    finally:
        session.close()
        conn.close()

    return "", 200


@application.route("/lifecycle/coreos-install/fail/<string:request_raw_query>", methods=["POST"])
def lifecycle_post_coreos_install_fail(request_raw_query):
    conn, session = smart.create_conn_with_session()
    try:
        i = crud.InjectLifecycle(session, request_raw_query=request_raw_query)
        i.refresh_lifecycle_coreos_install(False)
    finally:
        session.close()
        conn.close()
    return "", 200


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
    conn, session = smart.create_conn_with_session()
    try:
        d = ops.healthz(application, session, request)
    finally:
        session.close()
        conn.close()
    return jsonify(d)


@application.route('/discovery', methods=['POST'])
def discovery():
    err = jsonify({u'boot-info': {}, u'lldp': {}, u'interfaces': []}), 406
    try:
        r = json.loads(request.get_data())
    except (KeyError, TypeError, ValueError):
        return err

    conn, session = smart.create_conn_with_session()
    try:
        i = crud.InjectDiscovery(session,
                                 ignition_journal=ignition_journal,
                                 discovery=r)
        new = i.commit()
        cache.delete(request.path)
        d = jsonify({"total_elt": new[0], "new": new[1]})
    except TypeError:
        d = err
    finally:
        session.close()
        conn.close()
    return d


@application.route('/discovery', methods=['GET'])
def discovery_get():
    all_data = cache.get(request.path)
    if all_data is None:
        conn, session = smart.create_conn_with_session()
        try:
            fetch = crud.FetchDiscovery(session, ignition_journal=ignition_journal)
            all_data = fetch.get_all()
            cache.set(request.path, all_data, timeout=30)
        finally:
            session.close()
            conn.close()
    return jsonify(all_data)


@application.route('/scheduler', methods=['GET'])
def scheduler_get():
    all_data = cache.get(request.path)
    if all_data is None:
        conn, session = smart.create_conn_with_session()
        try:
            fetch = crud.FetchSchedule(session)
            all_data = fetch.get_schedules()
            cache.set(request.path, all_data, timeout=30)
        finally:
            session.close()
            conn.close()

    return jsonify(all_data)


@application.route('/scheduler/<string:role>', methods=['GET'])
def get_schedule_by_role(role):
    conn, session = smart.create_conn_with_session()
    try:
        fetch = crud.FetchSchedule(session)
        multi = role.split("&")
        data = fetch.get_roles(*multi)
    finally:
        session.close()
        conn.close()

    return jsonify(data)


@application.route('/scheduler/available', methods=['GET'])
def get_available_machine():
    conn, session = smart.create_conn_with_session()
    try:
        fetch = crud.FetchSchedule(session)
        data = fetch.get_available_machines()
    finally:
        session.close()
        conn.close()

    return jsonify(data)


@application.route('/scheduler/ip-list/<string:role>', methods=['GET'])
def get_schedule_role_ip_list(role):
    conn, session = smart.create_conn_with_session()
    try:
        fetch = crud.FetchSchedule(session)
        ip_list_role = fetch.get_role_ip_list(role)
    finally:
        session.close()
        conn.close()

    return jsonify(ip_list_role)


@application.route('/scheduler', methods=['POST'])
def scheduler_post():
    try:
        r = json.loads(request.get_data())
    except ValueError:
        return jsonify(
            {
                u"roles": model.ScheduleRoles.roles,
                u'selector': {
                    u"mac": ""
                }
            }), 406

    conn, session = smart.create_conn_with_session()
    try:
        inject = crud.InjectSchedule(session, data=r)
        inject.apply_roles()
        inject.commit()
    finally:
        session.close()
        conn.close()

    cache.delete(request.path)
    return jsonify(r)


@application.route('/backup/db', methods=['POST'])
def backup_database():
    if "sqlite://" in ec.db_uri:
        return ops.backup_sqlite(cache=cache, application=application)
    return jsonify({"NotImplementedError": "%s" % ec.api_uri}), 404


@application.route('/discovery/interfaces', methods=['GET'])
def discovery_interfaces():
    conn, session = smart.create_conn_with_session()
    try:
        fetch = crud.FetchDiscovery(session, ignition_journal=ignition_journal)
        interfaces = fetch.get_all_interfaces()
    finally:
        session.close()
        conn.close()

    return jsonify(interfaces)


@application.route('/discovery/ignition-journal/<string:uuid>/<string:boot_id>', methods=['GET'])
def discovery_ignition_journal_by_boot_id(uuid, boot_id):
    conn, session = smart.create_conn_with_session()
    try:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal(uuid, boot_id=boot_id)
    finally:
        session.close()
        conn.close()

    return jsonify(lines)


@application.route('/discovery/ignition-journal/<string:uuid>', methods=['GET'])
def discovery_ignition_journal_by_uuid(uuid):
    conn, session = smart.create_conn_with_session()
    try:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal(uuid)
    finally:
        session.close()
        conn.close()

    return jsonify(lines)


@application.route('/discovery/ignition-journal', methods=['GET'])
def discovery_ignition_journal_summary():
    conn, session = smart.create_conn_with_session()
    try:
        fetch = crud.FetchDiscovery(session,
                                    ignition_journal=ignition_journal)
        lines = fetch.get_ignition_journal_summary()
    finally:
        session.close()
        conn.close()

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
        matchbox_resp = requests.get(
            "%s%s" % (
                app.config["MATCHBOX_URI"],
                request.full_path))
        matchbox_resp.close()
        response = matchbox_resp.content.decode()
        return Response(response, status=200, mimetype="text/plain")

    except requests.exceptions.ConnectionError as e:
        app.logger.warning("404 for /ipxe")
        return "404", 404


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
    conn, session = smart.create_conn_with_session()

    if all_data is None:
        disco = crud.FetchDiscovery(session, ignition_journal=ignition_journal)
        all_data = disco.get_all()
        cache.set(key, all_data, timeout=30)

    res = [["Created", "cidr-boot", "mac-boot", "fqdn", "Roles", "Installed", "Up-to-date", "Rolling"]]
    try:
        for i in all_data:
            sub_list = list()
            sub_list.append(i["boot-info"]["created-date"])
            for j in i["interfaces"]:
                if j["as_boot"]:
                    sub_list.append(j["cidrv4"])
                    sub_list.append(j["mac"])
                    sub_list.append(j["fqdn"])
                    try:
                        schedule = crud.FetchSchedule(session)
                        roles = schedule.get_roles_by_mac_selector(j["mac"])
                        if not roles:
                            raise NotImplementedError
                        sub_list.append(roles)
                    except Exception as e:
                        sub_list.append("NoRole")

                    life = crud.FetchLifecycle(session)
                    installed = life.get_coreos_install_status(j["mac"])
                    if installed is None:
                        for i in ["PendingInstall", "PendingBoot", "ForeignDisabled"]:
                            sub_list.append(i)
                    else:
                        sub_list.append(installed)
                        ignition = life.get_ignition_uptodate_status(j["mac"])
                        if ignition is None:
                            ignition = "PendingBoot"
                        sub_list.append(ignition)

                        rolling = life.get_rolling_status(j["mac"])
                        if rolling is None:
                            rolling = "ForeignDisabled"
                        sub_list.append(rolling)
            res.append(sub_list)
    finally:
        session.close()
        conn.close()

    return jsonify(res)


if __name__ == "__main__":
    app.logger.setLevel("DEBUG")
    application.run(debug=True)
