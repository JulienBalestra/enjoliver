import time
from contextlib import contextmanager

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

    def __new__(cls, *args, **kwargs):
        if args[0] in cls._instances:
            return cls._instances[args[0]]

        o = object.__new__(cls)
        cls._instances[args[0]] = o
        return o

    @once
    def __init__(self, endpoint: str):
        self._endpoint = endpoint
        self.request_latency = Histogram("%s_latency" % self.endpoint, "Histogram of request latency",
                                         ['method', 'endpoint'])
        self.request_count = Counter("%s_requests_count" % self.endpoint, "Counter of number requests done",
                                     ['method', 'endpoint', 'http_status'])

    @property
    def endpoint(self):
        return self._endpoint

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__, self.endpoint)

    def before(self):
        request.start_time = time.time()

    def after(self, response):
        request_latency = time.time() - request.start_time
        self.request_latency.labels(request.method, request.url_rule.rule).observe(request_latency)
        self.request_count.labels(request.method, request.url_rule.rule, response.status_code).inc()
        return response


class DatabaseMonitoringComponents:
    _instances = dict()
    _init = False

    def __new__(cls, *args, **kwargs):
        if args[0] in cls._instances:
            return cls._instances[args[0]]

        o = object.__new__(cls)
        cls._instances[args[0]] = o
        return o

    @once
    def __init__(self, endpoint: str):
        self._endpoint = endpoint
        self.request_latency = Histogram("%s_latency" % self.endpoint, "Histogram of request latency",
                                         ['endpoint'])
        self.request_count = Counter("%s_requests_count" % self.endpoint, "Counter of number requests done",
                                     ['endpoint'])
        self.connection_error_count = Counter("%s_connection_error_count" % self.endpoint,
                                              "Counter of number connection error done", ['engine_url'])
        self.error_during_session = Counter("%s_error_during_session_count" % self.endpoint,
                                            "Counter of number error during session done", ['engine_url', "exception"])

    @property
    def endpoint(self):
        return self._endpoint

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__, self.endpoint)

    def connection_error(self, engine_url: str):
        self.connection_error_count.labels(engine_url).inc()

    @contextmanager
    def observe_session(self, engine_url: str):
        start = time.time()
        try:
            yield
        except Exception as e:
            self.error_during_session.labels(engine_url, type(e).__name__).inc()
        finally:
            latency = time.time() - start
            self.request_latency.labels(engine_url).observe(latency)
            self.request_count.labels(engine_url).inc()


class CockroachDatabase:
    _instance = None
    _init = False

    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance

        o = object.__new__(cls)
        cls._instance = o
        return o

    @once
    def __init__(self):
        self.retry_count = Counter("cockroachdb_txn_retry_count", "Counter of transaction retry done")

    def transaction_retry_inc(self):
        self.retry_count.inc()
