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

"""Interface to PostgresQL for Zoe state."""

import logging

from zoe_lib.state.base import BaseTable, BaseRecord

log = logging.getLogger(__name__)


class Quota(BaseRecord):
    """A quota object describes limits imposed to users on resource usage."""

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.name = d['name']
        self.concurrent_executions = d['concurrent_executions']
        self.memory = d['memory']
        self.cores = d['cores']
        self.runtime_limit = d['runtime_limit']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'concurrent_executions': self.concurrent_executions,
            'cores': self.cores,
            'memory': self.memory,
            'runtime_limit': self.runtime_limit
        }

    def set_concurrent_executions(self, value):
        """Setter for concurrent execution limit."""
        self.concurrent_executions = value
        self.sql_manager.quota_update(self.id, concurrent_executions=value)

    def set_memory(self, value):
        """Setter for memory limit."""
        self.memory = value
        self.sql_manager.quota_update(self.id, memory=value)

    def set_cores(self, value):
        """Setter for cores limit."""
        self.cores = value
        self.sql_manager.quota_update(self.id, cores=value)

    def set_runtime_limit(self, value):
        """Setter for the runtime limit."""
        self.runtime_limit = value
        self.sql_manager.quota_update(self.id, runtime_limit=value)

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Quota):
            return self.id == other.id
        else:
            return False


class QuotaTable(BaseTable):
    """Abstraction for the quota table in the database."""
    def __init__(self, sql_manager):
        super().__init__(sql_manager, "quota")

    def create(self):
        """Create the quota table."""
        self.cursor.execute('''CREATE TABLE quota (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            concurrent_executions INT NOT NULL,
            memory BIGINT NOT NULL,
            cores INT NOT NULL,
            runtime_limit INT NOT NULL
        )''')
        self.cursor.execute('''INSERT INTO quota (id, name, concurrent_executions, memory, cores, runtime_limit) VALUES (DEFAULT, 'default', 5, 34359738368, 20, 24)''')

    def select(self, only_one=False, **kwargs):
        """
        Return a list of quotas.

        :param only_one: only one result is expected
        :type only_one: bool
        :param kwargs: filter services based on their fields/columns
        :return: one or more ports
        """
        q_base = 'SELECT * FROM quota'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for key, value in kwargs.items():
                filter_list.append('{} = %s'.format(key))
                args_list.append(value)
            q += ' AND '.join(filter_list)
            query = self.cursor.mogrify(q, args_list)
        else:
            query = self.cursor.mogrify(q_base)

        self.cursor.execute(query)
        if only_one:
            row = self.cursor.fetchone()
            if row is None:
                return None
            return Quota(row, self.sql_manager)
        else:
            return [Quota(x, self.sql_manager) for x in self.cursor]

    def insert(self, name, concurrent_executions, memory, cores, runtime_limit):
        """Adds a new quota to the state."""
        query = self.cursor.mogrify('INSERT INTO quota (id, name, concurrent_executions, memory, cores, runtime_limit) VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id', (name, concurrent_executions, memory, cores, runtime_limit))
        self.cursor.execute(query)
        self.sql_manager.commit()
        return self.cursor.fetchone()[0]

    def delete(self, record_id):
        """Delete a quota from the state."""
        query = 'UPDATE "user" SET quota_id = (SELECT id from quota WHERE name=\'default\') WHERE quota_id=%s'
        self.cursor.execute(query, (record_id,))
        query = "DELETE FROM quota WHERE id = %s"
        self.cursor.execute(query, (record_id,))
        self.sql_manager.commit()
