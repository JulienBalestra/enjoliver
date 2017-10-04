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
