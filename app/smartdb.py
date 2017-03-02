import abc


class SmartClient(object):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def parse_db_uri(uri):
        if "cockroach://" in uri:
            # split
            return _MultipleEndpoints
        return _SingleEndpoint

    def __new__(cls, db_uri):
        o = object.__new__(cls.parse_db_uri(db_uri))
        o.__init__(db_uri)
        return o

    def __init__(self, input_data):
        self.input_data = input_data

    @abc.abstractmethod
    def create_session(self):
        return

    @abc.abstractmethod
    def close(self):
        return


class _SingleEndpoint(SmartClient):
    def create_session(self):
        pass


class _MultipleEndpoints(SmartClient):
    def create_session(self):
        pass
