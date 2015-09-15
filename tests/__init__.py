import pytest

from zoe_scheduler.state import Base, _engine


@pytest.fixture(scope='function')
def sqlalchemy(request):
    Base.metadata.create_all(_engine)