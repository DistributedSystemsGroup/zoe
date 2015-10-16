# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

import pytest

from common.configuration import conf_init


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
