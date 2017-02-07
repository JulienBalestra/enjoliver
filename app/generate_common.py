import abc
import json
import os

import logger


class GenerateCommon(object):
    """
    Common set of methods used to generate groups and profiles
    """

    __metaclass__ = abc.ABCMeta

    _target_data = None
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
