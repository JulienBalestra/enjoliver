import abc
import json
import os

import logger


class GenerateCommon(object):
    """
    Common set of methods used to generate groups and profiles
    """

    __metaclass__ = abc.ABCMeta

    app_path = "%s" % os.path.dirname(__file__)
    project_path = os.path.split(app_path)[0]
    bootcfg_path = "%s/bootcfg" % project_path

    _target_data = None
    _api_uri = None
    _raise_enof = IOError

    log = logger.get_logger("Generator")

    @abc.abstractmethod
    def generate(self):
        return

    @property
    def target_data(self):
        if self._target_data is not None:
            return self._target_data
        return self.generate()

    @property
    def api_uri(self):
        """
        :rtype: str
        :return: URI address
        """
        if self._api_uri is not None:
            self.log.debug("return %s" % self._api_uri)
            return self._api_uri
        api_uri = os.getenv("API_URI", None)
        if api_uri is not None:
            self._api_uri = api_uri
            self.log.debug("env -> API_URI=%s" % self._api_uri)
        else:
            raise AttributeError("API_URI == %s" % api_uri)

        return self._api_uri

    def render(self, indent=2):
        self.generate()
        return json.dumps(self._target_data, indent=indent)

    def dump(self):
        with open("%s/%s.json" % (self.target_path, self.target_data["id"]), "w") as fd:
            fd.write(self.render())

    @staticmethod
    def ensure_directory(path):
        if os.path.isdir(path) is False:
            raise IOError("%s not a valid as directory" % path)
        return path

    def ensure_file(self, path):
        if os.path.isfile(path) is False:
            raise self._raise_enof("%s not a valid as file" % path)
        return path
