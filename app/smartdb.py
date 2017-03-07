"""
Always give a working freshly connected session
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import logger
import model


class SmartClient(object):
    engines = []
    log = logger.get_logger(__file__)
    last_shuffle = 0

    @staticmethod
    def parse_db_uri(db_uri):
        if "cockroachdb://" in db_uri and db_uri.count(",") > 1:
            return _MultipleEndpoints
        return _SingleEndpoint

    def __new__(cls, db_uri):
        o = object.__new__(cls.parse_db_uri(db_uri))
        return o

    def __init__(self, db_uri):
        self._create_engines(db_uri.split(","))

    def _create_engines(self, uri_list):
        for single_uri in uri_list:
            e = create_engine(single_uri)
            if "%s" % e.url not in self.engine_urls:
                self.log.info("%s %s" % (e.driver, e.url))
                self.engines.append(e)
        self.log.info("total: %d" % len(self.engines))

    @contextmanager
    def connected_session(self):
        conn = self.get_engine_connection()
        Session = sessionmaker(bind=conn)
        session = Session(bind=conn)
        try:
            yield session
        finally:
            session.close()
            conn.close()

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
        model.BASE.metadata.create_all(self.get_engine_connection())


class _SingleEndpoint(SmartClient):
    pass


class _MultipleEndpoints(SmartClient):
    pass
