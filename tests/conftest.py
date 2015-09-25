import json

import pytest

from zoe_scheduler.state import init as state_init, Base, AlchemySession
from zoe_client.state.application import ApplicationState
from zoe_scheduler.application_description import ZoeApplication
from zoe_scheduler.configuration import init as conf_init, scheduler_conf


def pytest_addoption(parser):
    parser.addoption("--test-environment", default="local", help="Test environment: 'local' or 'travis'")


@pytest.fixture(scope='session')
def environment(request):
    return request.config.getoption("--test-environment")


@pytest.fixture(scope='session')
def configuration(environment):
    if environment == 'local':
        conf_init('tests/resources/zoe-local.conf')
    else:
        conf_init('tests/resources/zoe-travis.conf')


@pytest.fixture(scope='session')
def state_connection(request, configuration):
    engine = state_init(scheduler_conf().db_url)
    connection = engine.connect()
    trans = connection.begin()

    Base.metadata.create_all(connection)

    def fin():
        trans.rollback()
        connection.close()
        engine.dispose()
    request.addfinalizer(fin)

    return connection


@pytest.fixture(scope='function')
def state_session(state_connection, request):
    inner_trans = state_connection.begin_nested()
    session = AlchemySession(bind=state_connection)

    def fin():
        session.close()
        inner_trans.rollback()
    request.addfinalizer(fin)

    return session


@pytest.fixture(scope='function')
def application(state_session, notebook_test):
    app = ApplicationState()
    app.user_id = 1
    app.description = ZoeApplication.from_dict(notebook_test)
    state_session.add(app)

    state_session.flush()
    return app


@pytest.fixture(scope='session')
def notebook_test():
    jsondata = open("tests/resources/spark-notebook-test.json", "r")
    dictdata = json.load(jsondata)
    return dictdata
