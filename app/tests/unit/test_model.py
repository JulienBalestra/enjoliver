import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import model

POST_ONE = {
    "boot-info": {
        "mac": "52:54:00:99:38:e9",
        "uuid": "4422974d-687c-4df2-98b8-95fdf465f0f6"
    },
    "lldp": {
        "data": {
            "interfaces": [
                {
                    "chassis": {
                        "id": "28:f1:0e:12:20:00",
                        "name": "rkt-12409f1e-aa8b-47de-8906-fae5be63c808"
                    },
                    "port": {
                        "id": "fe:54:00:99:38:e9"
                    },
                    "name": "eth0"
                }
            ]
        },
        "is_file": True
    },
    "interfaces": [
        {
            "name": "lo",
            "mac": "",
            "netmask": 8,
            "cidrv4": "127.0.0.1/8",
            "ipv4": "127.0.0.1"
        },
        {
            "name": "eth0",
            "mac": "52:54:00:99:38:e9",
            "netmask": 21,
            "cidrv4": "172.20.0.91/21",
            "ipv4": "172.20.0.91"
        }
    ],
    "ignition-journal": None
}


class TestModel(unittest.TestCase):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path
    session = None

    @classmethod
    def setUpClass(cls):
        db = "%s/%s.sqlite" % (cls.dbs_path, TestModel.__name__.lower())
        try:
            os.remove(db)
        except OSError:
            pass
        engine = create_engine('sqlite:///%s' % db, echo=True)
        model.Base.metadata.create_all(engine)

        session = sessionmaker(bind=engine)
        cls.session = session()

    def test_00(self):
        model.insert_data(self.session, POST_ONE)
