from generate_groups import GenerateGroup
from generate_profiles import GenerateProfile


class Generator(object):
    """
    Generator ensure the coherence from group -> profile -> ignition
    """

    def __init__(self, profile_id, name, ignition_id, bootcfg_path,
                 selector=None, group_id=None, extra_metadata=None):
        self.profile = GenerateProfile(
            _id=profile_id,
            name=name,
            ignition_id=ignition_id,
            bootcfg_path=bootcfg_path)

        self.group = GenerateGroup(
            _id=group_id if group_id else profile_id,
            name=name,
            profile=profile_id,  # TODO
            selector=selector,
            metadata=extra_metadata,
            bootcfg_path=bootcfg_path)

    def generate_profile(self):
        return self.profile.generate()

    def generate_group(self):
        return self.group.generate()

    def dumps(self):
        self.profile.dump()
        self.group.dump()
