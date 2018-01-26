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


class Role(BaseRecord):
    """A role object describes the permissions of groups of users."""

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.name = d['name']
        self.can_see_status = d['can_see_status']
        self.can_change_config = d['can_change_config']
        self.can_operate_others = d['can_operate_others']
        self.can_delete_executions = d['can_delete_executions']
        self.can_access_api = d['can_access_api']
        self.can_customize_resources = d['can_customize_resources']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'can_see_status': self.can_see_status,
            'can_change_config': self.can_change_config,
            'can_operate_others': self.can_operate_others,
            'can_delete_executions': self.can_delete_executions,
            'can_access_api': self.can_access_api,
            'can_customize_resources': self.can_customize_resources
        }


class RoleTable(BaseTable):
    """Abstraction for the role table in the database."""
    def __init__(self, sql_manager):
        super().__init__(sql_manager, "role")

    def create(self):
        """Create the role table."""
        self.cursor.execute('''CREATE TABLE role (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            can_see_status BOOLEAN NOT NULL DEFAULT FALSE,
            can_change_config BOOLEAN NOT NULL DEFAULT FALSE,
            can_operate_others BOOLEAN NOT NULL DEFAULT FALSE,
            can_delete_executions BOOLEAN NOT NULL DEFAULT FALSE,
            can_access_api BOOLEAN NOT NULL DEFAULT FALSE,
            can_customize_resources BOOLEAN NOT NULL DEFAULT FALSE
        )''')
        self.cursor.execute('''INSERT INTO role (id, name, can_see_status, can_change_config, can_operate_others, can_delete_executions, can_access_api, can_customize_resources) VALUES (DEFAULT, 'admin', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE)''')
        self.cursor.execute('''INSERT INTO role (id, name, can_see_status, can_access_api, can_customize_resources) VALUES (DEFAULT, 'superuser', TRUE, TRUE, TRUE)''')
        self.cursor.execute('''INSERT INTO role (id, name) VALUES (DEFAULT, 'user')''')

    def select(self, only_one=False, **kwargs):
        """
        Return a list of roles.

        :param only_one: only one result is expected
        :type only_one: bool
        :param kwargs: filter services based on their fields/columns
        :return: one or more ports
        """
        q_base = 'SELECT * FROM role'
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
            return Role(row, self.sql_manager)
        else:
            return [Role(x, self.sql_manager) for x in self.cursor]

    def update(self, record_id, **kwargs):
        """Update the state of an existing role."""
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(record_id)
        q_base = 'UPDATE role SET ' + set_q + ' WHERE id=%s'
        query = self.cursor.mogrify(q_base, value_list)
        self.cursor.execute(query)
        self.sql_manager.commit()

    def insert(self, name):
        """Adds a new role to the state."""
        query = self.cursor.mogrify('INSERT INTO role (id, name) VALUES (DEFAULT, %s) RETURNING id', (name,))
        self.cursor.execute(query)
        self.sql_manager.commit()
        return self.cursor.fetchone()[0]

    def delete(self, role_id):
        """Delete a role from the state."""
        query = 'UPDATE "user" SET role_id = (SELECT id from role WHERE name=\'user\') WHERE role_id=%s'
        self.cursor.execute(query, (role_id,))
        query = "DELETE FROM role WHERE id = %s"
        self.cursor.execute(query, (role_id,))
        self.sql_manager.commit()
