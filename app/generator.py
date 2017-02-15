from generate_groups import GenerateGroup
from generate_profiles import GenerateProfile


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
