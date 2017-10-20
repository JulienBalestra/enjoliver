import os
import unittest

from unit import model_player

from app import configs
from app import smartdb
from repositories.register import RepositoriesRegister

EC = configs.EnjoliverConfig()


@unittest.skip("")
class TestModelSQLiteMemory(model_player.TestModel):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path

    @classmethod
    def setUpClass(cls):
        db_uri = 'sqlite:///:memory:'

        cls.smart = smartdb.SmartDatabaseClient(db_uri)
        cls.repositories = RepositoriesRegister(cls.smart)
        cls.set_up_class_checks(cls.smart)


# @unittest.skip("TODO")
class TestModelSQLiteFS(model_player.TestModel):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path
    ignition_journal_path = "%s/ignition_journal" % unit_path

    @classmethod
    def setUpClass(cls):
        db = "%s/%s.sqlite" % (cls.dbs_path, TestModelSQLiteMemory.__name__.lower())
        try:
            os.remove(db)
        except OSError:
            pass
        assert os.path.isfile(db) is False
        db_uri = 'sqlite:///%s' % db

        cls.smart = smartdb.SmartDatabaseClient(db_uri)
        cls.repositories = RepositoriesRegister(cls.smart)
        cls.set_up_class_checks(cls.smart)


@unittest.skip("TODO")
class TestModelCockroach(model_player.TestModel):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path

    @classmethod
    def setUpClass(cls):
        uris = [
            "cockroachdb://root@localhost:26257",
            "cockroachdb://root@localhost:26258",
            "cockroachdb://root@localhost:26259"
        ]
        db_uri = ",".join(uris)
        cls.smart = smartdb.SmartDatabaseClient(db_uri)
        cls.repositories = RepositoriesRegister(cls.smart)
        cls.set_up_class_checks(cls.smart)


@unittest.skip("TODO")
class TestModelPostgresql(model_player.TestModel):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path

    @classmethod
    def setUpClass(cls):
        db_uri = "postgresql://postgres@localhost:5432"
        cls.smart = smartdb.SmartDatabaseClient(db_uri)
        cls.repositories = RepositoriesRegister(cls.smart)
        cls.set_up_class_checks(cls.smart)
