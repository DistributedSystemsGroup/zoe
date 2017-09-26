# Copyright (c) 2017, Daniele Venzano
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

"""Mock SQL Manager for unit testing."""

import sqlite3
from collections import namedtuple

from zoe_lib.state.sql_manager import SQLManager


Conf = namedtuple('Conf', ['dbuser', 'dbpass', 'dbhost', 'dbport', 'dbname', 'deployment_name'])


class MockSQLManager(SQLManager):
    """A mock SQL manager."""
    def __init__(self):
        fake_conf = Conf(dbuser='', dbpass='', dbhost='', dbport=5432, dbname='', deployment_name='test')
        super().__init__(fake_conf)

    def _connect(self):
        self.conn = sqlite3.connect(':memory:')

    def _cursor(self):
        return self.conn.cursor()
