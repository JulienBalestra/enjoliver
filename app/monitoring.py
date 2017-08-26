import time

from flask import request
from prometheus_client import Counter, Histogram


def once(__init__):
    def wrapper(*args, **kwargs):
        self = args[0]
        if self._init is True:
            return

        __init__(*args, **kwargs)
        self._init = True

    return wrapper


class FlaskMonitoringComponents:
    _instances = dict()
    _init = False
    __name__ = "FlaskMonitoringComponents"

    def __new__(cls, *args, **kwargs):
        if args[0] in cls._instances:
            return cls._instances[args[0]]

        o = object.__new__(cls)
        cls._instances[args[0]] = o
        return o

    @once
    def __init__(self, route_name):
        route_name = route_name[1:].replace("/", "_").replace("-", "_")
        self.request_latency = Histogram("%s_latency" % route_name, "Gauge in progress requests",
                                         ['method', 'endpoint'])
        self.request_count = Counter("%s_requests_count" % route_name, "Counter of number requests done",
                                     ['method', 'endpoint', 'http_status'])
        self._route_name = route_name

    @property
    def route_name(self):
        return self._route_name

    def __repr__(self):
        return "<%s(%s)>" % (self.__name__, self.route_name)

    def before(self):
        request.start_time = time.time()

    def after(self, response):
        request_latency = time.time() - request.start_time
        self.request_latency.labels(request.method, request.path).observe(request_latency)
        self.request_count.labels(request.method, request.path, response.status_code).inc()
        return response
