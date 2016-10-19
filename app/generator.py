from generate_groups import GenerateGroup
from generate_profiles import GenerateProfile


class Generator(object):
    def __init__(self, _id, name, ignition_id, bootcfg_path, selector=None):
        self.profile = GenerateProfile(
            _id=_id,
            name=name,
            ignition_id=ignition_id,
            bootcfg_path=bootcfg_path)

        self.group = GenerateGroup(
            _id=_id,
            name=name,
            profile=_id,  # TODO
            selector=selector,
            bootcfg_path=bootcfg_path)

    def generate_profile(self):
        return self.profile.generate()

    def generate_group(self):
        return self.group.generate()

    def dumps(self):
        self.profile.dump()
        self.group.dump()
