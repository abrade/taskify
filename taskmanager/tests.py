import json as _json
import unittest
import transaction

import pyramid.testing as _testing

import sqlalchemy.orm as _orm
import sqlalchemy.types as _types

import taskmanager.models.taskmanager as _tm


def dummy_request(dbsession):
    return _testing.DummyRequest(dbsession=dbsession)


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.config = _testing.setUp(settings={
            'sqlalchemy.url': 'postgresql://localhost:5432/tm_test'
        })
        self.config.include('.models')
        settings = self.config.get_settings()

        from .models import (
            get_engine,
            get_session_factory,
            get_tm_session,
            )

        self.engine = get_engine(settings)
        session_factory = get_session_factory(self.engine)

        self.session = _orm.scoped_session(session_factory)#get_tm_session(session_factory, transaction.manager)

    def init_database(self):
        from .models.meta import Base
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        from .models.meta import Base

        _testing.tearDown()
#        transaction.abort()
        Base.metadata.drop_all(self.engine)


class TestWorker(BaseTest):

    def setUp(self):
        super(TestWorker, self).setUp()
        self.init_database()

        from .models import Worker

        from ipdb import set_trace as br; br()
        model = Worker('one', "OFFLINE")
        self.session.add(model)
        self.session.commit()

    def test_passing_view(self):
        from .views.workers import Workers
        info = Workers(_testing.DummyRequest()).get()
        self.assertEqual(info['result'], 'OK')
        print(info['data'])
        self.assertEqual(info['data'], 'taskmanager')


# class TestMyViewFailureCondition(BaseTest):

#     def test_failing_view(self):
#         from .views.default import my_view
#         info = my_view(dummy_request(self.session))
#         self.assertEqual(info.status_int, 500)
