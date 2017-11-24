# Copyright (c) 2016, Daniele Venzano
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

"""Interface to PostgresQL for Zoe state."""

import logging

log = logging.getLogger(__name__)


class BaseRecord:
    """
    :type sql_manager: SQLManager
    """
    def __init__(self, d, sql_manager):
        """
        :type sql_manager: SQLManager
        """
        self.sql_manager = sql_manager
        self.id = d['id']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        raise NotImplementedError


class BaseTable:
    """Common abstraction for all tables."""
    def __init__(self, sql_manager, table_name):
        self.table_name = table_name
        self.sql_manager = sql_manager
        self.cursor = self.sql_manager.cursor()

    def create(self):
        """Create this table."""
        raise NotImplementedError

    def insert(self, **kwargs):
        """Create a new record."""
        raise NotImplementedError

    def delete(self, record_id):
        """Delete a record from this table."""
        query = "DELETE FROM {} WHERE id = %s".format(self.table_name)
        self.cursor.execute(query, (record_id,))
        self.sql_manager.commit()

    def update(self, record_id, **kwargs):
        """Update the state of an execution."""
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(record_id)
        q_base = 'UPDATE {} SET '.format(self.table_name) + set_q + ' WHERE id=%s'
        query = self.cursor.mogrify(q_base, value_list)
        self.cursor.execute(query)
        self.sql_manager.commit()

    def select(self, only_one=False, limit=-1, **kwargs):
        """Select records."""
        raise NotImplementedError
