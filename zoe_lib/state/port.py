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

from zoe_lib.state.base import BaseRecord, BaseTable

log = logging.getLogger(__name__)


class Port(BaseRecord):
    """A tcp or udp port that should be exposed by the backend."""

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.internal_name = d['internal_name']
        self.external_ip = d['external_ip']
        self.external_port = d['external_port']
        self.description = d['description']

        self.internal_number = self.description['port_number']
        self.protocol = self.description['protocol']
        self.url_template = self.description['url_template']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'internal_name': self.internal_name,
            'external_ip': self.external_ip,
            'external_port': self.external_port,
            'description': self.description
        }

    def __eq__(self, other):
        return self.id == other.id

    def activate(self, ext_ip, ext_port):
        """The backend has exposed the port."""
        self.sql_manager.ports.update(self.id, external_ip=ext_ip, external_port=ext_port)
        self.external_port = ext_port
        self.external_ip = ext_ip

    def reset(self):
        """The backend has stopped exposing the port."""
        self.sql_manager.ports.update(self.id, external_ip=None, external_port=None)
        self.external_port = None
        self.external_ip = None


class PortTable(BaseTable):
    """Abstraction for the port table in the database."""
    def __init__(self, sql_manager):
        super().__init__(sql_manager, "port")

    def create(self):
        """Create the Port table."""
        self.cursor.execute('''CREATE TABLE port (
            id SERIAL PRIMARY KEY,
            service_id INT REFERENCES service ON DELETE CASCADE,
            internal_name TEXT NOT NULL,
            external_ip INET NULL,
            external_port INT NULL,
            description JSON NOT NULL
        )''')

    def insert(self, service_id, internal_name, description):
        """Adds a new port to the state."""
        query = self.cursor.mogrify('INSERT INTO port (id, service_id, internal_name, external_ip, external_port, description) VALUES (DEFAULT, %s, %s, NULL, NULL, %s) RETURNING id', (service_id, internal_name, description))
        self.cursor.execute(query)
        self.sql_manager.commit()
        return self.cursor.fetchone()[0]

    def select(self, only_one=False, limit=-1, **kwargs):
        """
        Return a list of ports.

        :param only_one: only one result is expected
        :type only_one: bool
        :param limit: limit the result to this number of entries
        :type limit: int
        :param kwargs: filter services based on their fields/columns
        :return: one or more ports
        """
        q_base = 'SELECT * FROM port'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for key, value in kwargs.items():
                filter_list.append('{} = %s'.format(key))
                args_list.append(value)
            q += ' AND '.join(filter_list)
            if limit > 0:
                q += ' ORDER BY id DESC LIMIT {}'.format(limit)
            query = self.cursor.mogrify(q, args_list)
        else:
            if limit > 0:
                q_base += ' ORDER BY id DESC LIMIT {}'.format(limit)
            query = self.cursor.mogrify(q_base)

        self.cursor.execute(query)
        if only_one:
            row = self.cursor.fetchone()
            if row is None:
                return None
            return Port(row, self.sql_manager)
        else:
            return [Port(x, self.sql_manager) for x in self.cursor]
