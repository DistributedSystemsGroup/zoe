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

from zoe_lib.state.base import BaseRecord, BaseTable

log = logging.getLogger(__name__)


class User(BaseRecord):
    """An user object describes a Zoe user."""

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.username = d['username']
        self.fs_uid = d['fs_uid']
        self.role = d['role']
        self.email = d['email']
        self.priority = d['priority']
        self.enabled = d['enabled']
        self.quota_id = d['quota_id']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'username': self.username,
            'fs_uid': self.fs_uid,
            'role': self.role,
            'email': self.email,
            'priority': self.priority,
            'enabled': self.enabled,
            'quota_id': self.quota_id
        }

    def set_email(self, new_email: str):
        """Update the email address for this user."""
        self.email = new_email
        self.sql_manager.user_update(self.id, email=new_email)

    def set_priority(self, new_priority: int):
        """Update the priority for this user."""
        self.priority = new_priority
        self.sql_manager.user_update(self.id, priority=new_priority)

    def set_enabled(self, enable: bool):
        """Enable or disable a user."""
        self.enabled = enable
        self.sql_manager.user_update(self.id, enabled=enable)

    def get_quota(self):
        """Get the quota for this user."""
        return self.sql_manager.quota_list(only_one=True, id=self.quota_id)

    def set_quota(self, quota_id):
        """Set a different quota for this user."""
        self.quota_id = quota_id
        self.sql_manager.user_update(self.id, quota_id=quota_id)

    def set_role(self, role):
        """Set a new role for this user."""
        self.role = role
        self.sql_manager.user_update(self.id, role=role)


class UserTable(BaseTable):
    """Abstraction for the user table in the database."""
    def __init__(self, sql_manager):
        super().__init__(sql_manager, "user")

    def create(self):
        """Create the user table."""
        self.cursor.execute('''CREATE TABLE "user" (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            fs_uid INT NOT NULL,
            email TEXT,
            priority SMALLINT NOT NULL DEFAULT 0,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            auth_source TEXT NOT NULL,
            role_id INT REFERENCES role,
            quota_id INT REFERENCES quota
        )''')
        self.cursor.execute('CREATE UNIQUE INDEX users_username_uindex ON "user" (username)')

    def select(self, only_one=False, **kwargs):
        """
        Return a list of users.

        :param only_one: only one result is expected
        :type only_one: bool
        :param kwargs: filter services based on their fields/columns
        :return: one or more ports
        """
        q_base = 'SELECT * FROM "user"'
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
            return User(row, self)
        else:
            return [User(x, self) for x in self.cursor]

    def update(self, port_id, **kwargs):
        """Update the state of an user port."""
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(port_id)
        q_base = 'UPDATE "user" SET ' + set_q + ' WHERE id=%s'
        query = self.cursor.mogrify(q_base, value_list)
        self.cursor.execute(query)
        self.sql_manager.commit()

    def insert(self, username, fs_uid, role, auth_source):
        """Adds a new user to the state."""
        query = self.cursor.mogrify('INSERT INTO "user" (id, username, fs_uid, email, priority, enabled, auth_source, role_id, quota_id) VALUES (DEFAULT, %s, %s, NULL, DEFAULT, DEFAULT, %s, (SELECT id FROM role WHERE name=%s), (SELECT id FROM quota WHERE name=\'default\')) RETURNING id', (username, fs_uid, auth_source, role))
        self.cursor.execute(query)
        self.sql_manager.commit()
        return self.cursor.fetchone()[0]
