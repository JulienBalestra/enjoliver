from generate_groups import GenerateGroup
from generate_profiles import GenerateProfile


class Generator(object):
    def __init__(self, _id, name, ignition_id, bootcfg_path):
        self.profile = GenerateProfile(
            _id=_id,
            name=name,
            ignition_id=ignition_id,
            bootcfg_path=bootcfg_path)

        self.group = GenerateGroup(
            _id=_id,
            name=name,
            profile=_id,  # TODO
            bootcfg_path=bootcfg_path)

    def dumps(self):
        self.profile.dump()
        self.group.dump()
