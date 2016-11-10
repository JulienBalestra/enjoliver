class Discovery(object):
    def __init__(self, new, cache_list):
        """
        :param new: Dict
        :param cache_list: Werkzeug Cache
        """

        self.new = new
        if cache_list:
            self.cache_list = cache_list
        else:
            self.cache_list = []

        self.mac = self._look_for_coherence(new)
        self.update = False

    @staticmethod
    def _look_for_coherence(new):
        try:
            mac = new["boot-info"]["mac"]
            interfaces = new["interfaces"]
            for i in interfaces:
                if i["MAC"] == mac:
                    return mac
        except (KeyError, TypeError):
            mac, interfaces = None, None

        raise LookupError("%s not found in interfaces list: %s" % (mac, interfaces))

    def _upsert(self):
        for elt in self.cache_list:
            if self.mac == elt["boot-info"]["mac"]:
                self.update = True
                # Change the address
                elt = self.new

        if self.update is False:
            self.cache_list.append(self.new)

    def refresh_cache(self):
        self._upsert()
        return self.cache_list

    @property
    def is_update(self):
        return self.update