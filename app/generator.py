import abc
import hashlib
import json
import os
import re

import logger
from configs import EnjoliverConfig

ec = EnjoliverConfig(importer=__file__)


class Generator(object):
    """
    Generator ensure the coherence from group -> profile -> ignition
    """

    def __init__(self,
                 api_uri,
                 profile_id,
                 name,
                 ignition_id,
                 matchbox_path,
                 selector=None,
                 group_id=None,
                 extra_metadata=None):
        self.profile = GenerateProfile(
            api_uri=api_uri,
            _id=profile_id,
            name=name,
            ignition_id=ignition_id,
            matchbox_path=matchbox_path)

        self.group = GenerateGroup(
            api_uri=api_uri,
            _id=group_id if group_id else profile_id,
            name=name,
            profile=profile_id,  # TODO
            selector=selector,
            metadata=extra_metadata,
            matchbox_path=matchbox_path)

    def generate_profile(self):
        return self.profile.generate()

    def generate_group(self):
        return self.group.generate()

    def dumps(self):
        self.profile.dump()
        self.group.dump()


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
        return json.dumps(self._target_data, indent=indent, sort_keys=True)

    def dump(self):
        file_path = "%s/%s.json" % (self.target_path, self.target_data["id"])
        try:
            with open(file_path, 'r') as f:
                on_disk = f.read()
            on_disk_hash = hashlib.sha256(on_disk).hexdigest()
        except Exception as e:
            self.log.warning("get hash of %s raise: %s %s" % (file_path, e, e.message))
            on_disk_hash = ""

        render = self.render()
        render_hash = hashlib.sha256(render).hexdigest()
        if render_hash != on_disk_hash:
            with open(file_path, "w") as fd:
                fd.write(render)
            self.log.info("replaced: %s" % file_path)
        else:
            self.log.debug("same hash -> %s" % file_path)

    @staticmethod
    def ensure_directory(path):
        if os.path.isdir(path) is False:
            raise IOError("%s not a valid as directory" % path)
        return path

    def ensure_file(self, path):
        if os.path.isfile(path) is False:
            raise self._raise_enof("%s not a valid as file" % path)
        return path


class GenerateProfile(GenerateCommon):
    def __repr__(self):
        return "GenProfile-%s" % self._target_data["id"]

    def __init__(self,
                 api_uri,
                 _id, name,
                 ignition_id,
                 matchbox_path):

        self.api_uri = api_uri
        self.ensure_directory(matchbox_path)
        self.ensure_directory("%s/ignition" % matchbox_path)
        try:
            self.ensure_file("%s/ignition/%s" % (matchbox_path, ignition_id))
        except Warning:
            self.log.warning("not here %s/ignition/%s\n" % (matchbox_path, ignition_id))

        self.target_path = self.ensure_directory("%s/profiles" % matchbox_path)
        self._target_data = {
            "id": "%s" % _id,
            "name": "%s" % name,
            "boot": {},
            "cloud_id": "",
            "ignition_id": "%s" % ignition_id
        }

    def _boot(self):
        if ec.assets_server_uri:
            self.log.debug("custom assets_server_uri=%s" % ec.assets_server_uri)
            uri = ec.assets_server_uri
        else:
            uri = self.api_uri
        self._target_data["boot"] = {
            "kernel": "%s%s" % (uri, ec.kernel),
            "initrd": ["%s%s" % (uri, ec.initrd)],
            "cmdline": {
                "coreos.config.url":
                    "%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}" % self.api_uri,
                "coreos.autologin": "",
                "coreos.first_boot": "",
                "coreos.oem.id": "pxe"
            }
        }

    def generate(self):
        self._boot()
        self.log.debug("done: %s" % self._target_data["name"])
        return self.target_data


class GenerateGroup(GenerateCommon):
    def __repr__(self):
        return "GenGroup[%s]" % self._target_data["id"]

    def __init__(self,
                 api_uri,
                 _id, name,
                 profile,
                 matchbox_path,
                 selector=None,
                 metadata=None,
                 ):
        self.api_uri = api_uri
        self.ensure_directory(matchbox_path)
        self.target_path = self.ensure_directory("%s/groups" % matchbox_path)
        self.ssh_authorized_keys_dir = "%s/ssh_authorized_keys" % matchbox_path
        self.extra_selector = None if not selector else dict(selector)
        self.extra_metadata = {} if not metadata else dict(metadata)

        self._target_data = {
            "id": _id,
            "name": name,
            "profile": profile,
            "metadata": {
                "api_uri": "",
                "etcd_initial_cluster": ""
            }
        }

    def _get_ssh_authorized_keys(self):
        keys = []

        if os.path.isdir(self.ssh_authorized_keys_dir) is False:
            return keys

        for k in os.listdir(self.ssh_authorized_keys_dir):
            fp = "%s/%s" % (self.ssh_authorized_keys_dir, k)
            with open(fp, 'r') as key:
                content = key.read()
            if len(content.split(" ")) < 2:
                self.log.debug("%s not valid as ssh_authorized_keys" % fp)
                continue
            keys.append(content)

        return keys

    def _metadata(self):
        self._target_data["metadata"]["api_uri"] = self.api_uri
        self._target_data["metadata"]["etcd_initial_cluster"] = ""  # default WET
        self._target_data["metadata"]["ssh_authorized_keys"] = self._get_ssh_authorized_keys()

        for k, v in self.extra_metadata.iteritems():
            self.log.debug("add %s: %s in metadata" % (k, v))
            self._target_data["metadata"][k] = v

    def _selector(self):
        if self.extra_selector is None:
            return

        if type(self.extra_selector) is not dict:
            raise TypeError("selector is not a dict")

        try:
            self.extra_selector["mac"] = self.extra_selector["mac"].lower()
            match = re.match(r"^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$",
                             self.extra_selector["mac"])
            if match is None:
                raise TypeError("%s is not a valid MAC address" % self.extra_selector["mac"].lower())
        except KeyError:
            pass

        self._target_data["selector"] = self.extra_selector
        self._target_data["metadata"]["selector"] = self.extra_selector

    def generate(self):
        self._metadata()
        self._selector()
        self.log.debug("done: %s" % self._target_data["id"])
        return self.target_data
