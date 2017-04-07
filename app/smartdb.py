"""
Always give a working freshly connected session
"""
from contextlib import contextmanager

import psycopg2
import psycopg2.errorcodes
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

import logger
import model


class SmartClient(object):
    log = logger.get_logger(__file__)

    engines = []
    lazy_engine = None

    @staticmethod
    def parse_db_uri(db_uri):
        if "cockroachdb://" in db_uri and db_uri.count(",") > 0:
            return _MultipleEndpoints
        return _SingleEndpoint

    def __new__(cls, db_uri):
        o = object.__new__(cls.parse_db_uri(db_uri))
        return o

    def __init__(self, db_uri):
        self._create_engines(db_uri.split(","))
        if isinstance(self, _SingleEndpoint):
            self.new_session = self.lazy_session
        else:
            self.new_session = self.connected_cockroach_session

    def _create_engines(self, uri_list):
        for single_uri in uri_list:
            e = create_engine(single_uri)
            if "%s" % e.url not in self.engine_urls:
                self.log.info("%s %s" % (e.driver, e.url))
                self.engines.append(e)
        self.log.info("total: %d" % len(self.engines))

    @contextmanager
    def connected_cockroach_session(self, snap=False):
        conn = self.get_engine_connection()
        try:
            with self.new_session_maker(conn) as sm:
                session = sm()
                if isinstance(self, _MultipleEndpoints) and snap:
                    session.execute(text("SET TRANSACTION ISOLATION LEVEL SNAPSHOT"))
                try:
                    yield session
                finally:
                    session.close()
        finally:
            conn.close()

    @contextmanager
    def new_session_maker(self, bind):
        sm = sessionmaker(bind)
        try:
            yield sm
        finally:
            sm.close_all()

    @contextmanager
    def new_session(self):
        raise NotImplementedError

    @contextmanager
    def lazy_session(self, snap=False):
        if not self.lazy_engine:
            self.lazy_engine = self.engines[0]
        with self.new_session_maker(self.lazy_engine) as sm:
            session = sm()
            try:
                yield session
            finally:
                session.close()

    @property
    def engine_urls(self):
        return ["%s" % k.url for k in self.engines]

    def get_engine_connection(self):
        for i, engine in enumerate(self.engines):
            try:
                conn = engine.connect()
                if conn.closed is False:
                    if i > 0:
                        self.log.info("moving reliable %s to index 0" % engine.url)
                        self.engines[0], self.engines[i] = self.engines[i], self.engines[0]
                    return conn
                self.log.warning("%d/%d could not connect to %s" % (i + 1, len(self.engines), engine.url))
            except Exception as e:
                self.log.warning("%d/%d could not connect to %s %s" % (i + 1, len(self.engines), engine.url, e))

        self.log.critical("could not connect to any of %s" % ",".join(self.engine_urls))
        raise ConnectionError(",".join(["%s" % k.url for k in self.engines]))

    def create_base(self):
        conn = self.get_engine_connection()
        try:
            model.BASE.metadata.create_all(conn)
        finally:
            conn.close()


class _SingleEndpoint(SmartClient):
    pass


class _MultipleEndpoints(SmartClient):
    pass


def cockroach_transaction(f):
    def run_transaction(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except DatabaseError as e:
                if not isinstance(e.orig, psycopg2.OperationalError) and \
                        not e.orig.pgcode == psycopg2.errorcodes.SERIALIZATION_FAILURE:
                    raise

    return run_transaction
