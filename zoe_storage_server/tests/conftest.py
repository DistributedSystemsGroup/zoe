import json

import pytest

from zoe_storage_server.configuration import conf_init


@pytest.fixture(scope='session')
def configuration(request):
    env = request.config.getoption("--test-environment")
    if env == 'local':
        return conf_init('tests/resources/zoe-local.conf')
    else:
        return conf_init('tests/resources/zoe-travis.conf')


@pytest.fixture(scope='session')
def notebook_test():
    jsondata = open("tests/resources/spark-notebook-test.json", "r")
    dictdata = json.load(jsondata)
    return dictdata
