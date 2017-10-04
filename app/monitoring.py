import os
from contextlib import contextmanager

import sys
import time
from flask import request, Flask, Response, g
from prometheus_client import Counter, Histogram, CollectorRegistry, multiprocess, generate_latest, CONTENT_TYPE_LATEST


def once(__init__):
    """
    Decorate the __init__ method of a class if you don't want to init a class twice when using a singleton
    The class have to embed a class variable named _init by default at False
    :param __init__:
    :return:
    """

    def wrapper(*args, **kwargs):
        self = args[0]
        if self._init is True:
            return

        __init__(*args, **kwargs)
        self._init = True

    return wrapper


class DatabaseMonitoring:
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
        self.request_latency = Histogram("enjoliver_db_request_duration_seconds", "Database request latency", ["caller"])
        self.request_count = Counter("enjoliver_db_request_total", "Database request count", ["caller"])
        self.cockroach_retry_count = Counter("enjoliver_cockroachdb_txn_retry_total", "CockroachDB transaction retry count",
                                             ['caller'])
        self.exception_count = Counter("enjoliver_db_exception_total", "Counter of number error during session",
                                       ["caller", "exception"])

    @contextmanager
    def observe_transaction(self, caller: str):
        """
        Wrapper to call around transaction against a database
        :param caller:
        :return:
        """
        start = time.time()
        try:
            yield
        except Exception as e:
            self.exception_count.labels(caller, type(e).__name__).inc()
            raise
        finally:
            latency = time.time() - start
            self.request_latency.labels(caller).observe(latency)
            self.request_count.labels(caller).inc()


def extract_exception_name(exc_info=None):
    """
    Function to get the exception name and module
    :param exc_info:
    :return:
    """
    if not exc_info:
        exc_info = sys.exc_info()
    return '{}.{}'.format(exc_info[0].__module__, exc_info[0].__name__)


def monitor_flask(app: Flask):
    """
    Add components to monitor each route with prometheus
    The monitoring is available at /metrics
    :param app: Flask application
    :return:
    """
    metrics = CollectorRegistry()

    def collect():
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
        return Response(data, mimetype=CONTENT_TYPE_LATEST)

    if "gunicorn" in os.getenv("SERVER_SOFTWARE", "") and os.getenv('prometheus_multiproc_dir'):
        app.add_url_rule('/metrics', 'metrics', collect)

    additional_kwargs = {
        'registry': metrics
    }
    request_latency = Histogram(
        'enjoliver_requests_duration_seconds',
        'Backend API request latency',
        ['method', 'path'],
        **additional_kwargs
    )
    request_count = Counter(
        'enjoliver_request_total',
        'Backend API request count',
        ['method', 'path'],
        **additional_kwargs
    )
    status_count = Counter(
        'enjoliver_responses_total',
        'Backend API response count',
        ['method', 'path', 'status_code'],
        **additional_kwargs
    )
    exception_count = Counter(
        'enjoliver_exceptions_total',
        'Backend API top-level exception count',
        ['method', 'path', 'type'],
        **additional_kwargs
    )

    @app.before_request
    def start_measure():
        g._start_time = time.time()
        request_count.labels(request.method, request.url_rule).inc()

    @app.after_request
    def count_status(response: Response):
        status_count.labels(request.method, request.url_rule, response.status_code).inc()
        request_latency.labels(request.method, request.url_rule).observe(time.time() - g._start_time)
        return response

    # Override log_exception to increment the exception counter
    def log_exception(exc_info):
        class_name = extract_exception_name(exc_info)
        exception_count.labels(request.method, request.url_rule, class_name).inc()
        app.logger.error('Exception on %s [%s]' % (
            request.path,
            request.method
        ), exc_info=exc_info)

    app.log_exception = log_exception
