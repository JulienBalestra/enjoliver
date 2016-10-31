import os
import urllib2

from flask import Flask, request, json

app = application = Flask(__name__)

application.config["BOOTCFG_URI"] = os.getenv(
    "BOOTCFG_URI", "http://127.0.0.1:8080")

application.config["BOOTCFG_URLS"] = [
    "/",
    "/boot.ipxe",
    "/boot.ipxe.0",
    "/assets"
]


@application.route('/', methods=['GET'])
def root():
    """
    Map the API
    :return: available routes
    """
    links = [k.rule for k in app.url_map.iter_rules()
             if "/static/" != k.rule[:8]]

    return json.jsonify(links)


@application.route('/healthz', methods=['GET'])
def healthz():
    """
    Query all services and return the status
    :return: json
    """
    status = {
        "global": True,
        "flask": True,
        "bootcfg": {
            k: False for k in application.config["BOOTCFG_URLS"]}
    }
    for k in status["bootcfg"]:
        try:
            bootcfg_resp = urllib2.urlopen(
                "%s%s" % (app.config["BOOTCFG_URI"], k))
            assert bootcfg_resp.code == 200
            status["bootcfg"][k] = True
        except Exception:
            status["bootcfg"][k] = False
            status["global"] = False

    return json.jsonify(status)


@application.route('/discovery', methods=['POST'])
def discovery():
    return "thank-you\n"


@application.route('/boot.ipxe', methods=['GET'])
@application.route('/boot.ipxe.0', methods=['GET'])
def boot_ipxe():
    """
    Replace the bootcfg/boot.ipxe by insert retry for dhcp and full URL for the chain
    :return: str
    """
    try:
        flask_uri = "%s://%s" % (
            request.environ.get('wsgi.url_scheme'),
            request.environ.get('HTTP_HOST'))
    except Exception:
        flask_uri = application.config["BOOTCFG_URI"]

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
    return response


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
        # [ipxe, kernel, initrd, boot]
        if len(resp_list) == 4:
            resp_list.insert(1, "echo start /ipxe\n")
            # resp_list.insert(2, ":retry_dhcp\n")
            # resp_list.insert(3, "dhcp || reboot\n")
        else:
            app.logger.warning("iPXE response is not coherent")

        return "".join(resp_list), 200

    except urllib2.URLError:
        return "404", 404


@app.errorhandler(404)
def page_not_found(error):
    return '404\n', 404


if __name__ == "__main__":
    application.run(debug=True)
