import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import model
import posts


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
        engine = create_engine('sqlite:///%s' % db)
        model.Base.metadata.create_all(engine)

        session = sessionmaker(bind=engine)
        cls.session = session()

    def test_00(self):
        i = model.Inject(self.session, posts.M1)
        i.commit()

    def test_01(self):
        i = model.Inject(self.session, posts.M2)
        i.commit()
        i = model.Inject(self.session, posts.M2)
        i.commit()
        i.commit()

    def test_02(self):
        for p in posts.ALL:
            i = model.Inject(self.session, p)
            i.commit()

    def test_03(self):
        for p in posts.ALL:
            i = model.Inject(self.session, p)
            i.commit()
