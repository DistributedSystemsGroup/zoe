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

import pytest
import json

from zoe_master.config import load_configuration, get_conf
from zoe_master.state.manager import StateManager
from zoe_master.state.blobs.fs import FSBlobs


class TestConf:
    def __init__(self):
        self.debug = True
        self.zk = 'zk:2181'
        self.state_dir = '/tmp/zoe'
        self.zoeadmin_password = 'test'
        self.passlib_rounds = 1
        self.enable_influxdb = False


@pytest.fixture(scope='session')
def configuration(request):
    load_configuration(test_conf=TestConf())
    return get_conf()


@pytest.fixture(scope='session')
def application_dict():
    jsondata = open("zoe_master/tests/resources/spark-wordcount-test.json", "r")
    return json.load(jsondata)


@pytest.fixture(scope='function')
def state_manager(configuration):
    return StateManager(FSBlobs)
