import logging
import socket

from configs import EnjoliverConfig

logger = logging.getLogger(__file__)
EC = EnjoliverConfig()


def get_mac_from_raw_query(request_raw_query: str):
    """
    Get MAC address inside a matchbox "request raw query"
    /path?<request_raw_query>
    :param request_raw_query:
    :return: mac address
    """
    mac = ""
    raw_query_list = request_raw_query.split("&")
    for param in raw_query_list:
        if "mac=" in param:
            mac = param.replace("mac=", "")
    if not mac:
        raise AttributeError("%s is not parsable" % request_raw_query)
    return mac.replace("-", ":")


def get_verified_dns_query(interface: dict):
    """
    A discovery machine give a FQDN. This method will do the resolution before insert in the db
    :param interface:
    :return:
    """
    fqdn = []
    try:
        for name in interface["fqdn"]:
            try:
                r = socket.gethostbyaddr(interface["ipv4"])[0]
                logger.debug("succeed to make dns request for %s:%s" % (interface["ipv4"], r))
                if name[-1] == ".":
                    name = name[:-1]

                if name == r:
                    fqdn.append(name)
                else:
                    logger.warning("fail to verify domain name discoveryC %s != %s socket.gethostbyaddr for %s %s" % (
                        name, r, interface["ipv4"], interface["mac"]))
            except socket.herror:
                logger.error("Verify FAILED '%s':%s socket.herror returning None" % (name, interface["ipv4"]))
                if EC.discovery_fqdn_verify is False:
                    logger.warning("Adding a non verified fqdn entry: %s" % name)
                    fqdn.append(name)

    except (KeyError, TypeError):
        logger.warning("No fqdn for %s returning None" % interface["ipv4"])

    if fqdn and len(fqdn) > 1:
        raise AttributeError("Should be only one: %s" % fqdn)
    return fqdn[0] if fqdn else None
