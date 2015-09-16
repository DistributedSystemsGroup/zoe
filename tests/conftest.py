import pytest

from common.application_resources import SparkApplicationResources

from zoe_scheduler.state import init as state_init, Base, AlchemySession
from zoe_scheduler.state.application import SparkSubmitApplicationState
from zoe_scheduler.state import UserState

from common.configuration import init as conf_init, zoeconf


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
    engine = state_init(zoeconf().db_url)
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
def application(state_session):
    user = UserState()
    user.email = 'a@b.c'

    app = SparkSubmitApplicationState()
    app.submit_image = "test"
    app.worker_image = "test"
    app.master_image = "test"
    app.name = "testapp"
    app.user = user
    app.required_resources = SparkApplicationResources()
    state_session.add(app)

    state_session.flush()
    return app
