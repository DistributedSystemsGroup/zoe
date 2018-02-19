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
        self.email = d['email']
        self.priority = d['priority']
        self.enabled = d['enabled']
        self.auth_source = d['auth_source']
        self.role_id = d['role_id']
        self.quota_id = d['quota_id']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'username': self.username,
            'fs_uid': self.fs_uid,
            'email': self.email,
            'priority': self.priority,
            'enabled': self.enabled,
            'auth_source': self.auth_source,
            'quota_id': self.quota_id,
            'role_id': self.role_id
        }

    def set_email(self, new_email: str):
        """Update the email address for this user."""
        self.email = new_email
        self.sql_manager.user.update(self.id, email=new_email)

    def set_priority(self, new_priority: int):
        """Update the priority for this user."""
        self.priority = new_priority
        self.sql_manager.user.update(self.id, priority=new_priority)

    def set_enabled(self, enable: bool):
        """Enable or disable a user."""
        self.enabled = enable
        self.sql_manager.user.update(self.id, enabled=enable)

    def set_quota_id(self, quota_id):
        """Set a different quota for this user."""
        self.quota_id = quota_id
        self.sql_manager.user.update(self.id, quota_id=quota_id)

    def set_role_id(self, role_id):
        """Set a new role for this user."""
        self.role_id = role_id
        self.sql_manager.user.update(self.id, role_id=role_id)

    @property
    def role(self):
        """Get the role from the DB."""
        return self.sql_manager.role.select(only_one=True, id=self.role_id)

    @property
    def quota(self):
        """Get the quota for this user."""
        return self.sql_manager.quota.select(only_one=True, id=self.quota_id)


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
            return User(row, self.sql_manager)
        else:
            return [User(x, self.sql_manager) for x in self.cursor]

    def insert(self, username, fs_uid, role, quota, auth_source):
        """Adds a new user to the state."""
        query = self.cursor.mogrify('INSERT INTO "user" (id, username, fs_uid, email, priority, enabled, auth_source, role_id, quota_id) VALUES (DEFAULT, %s, %s, NULL, DEFAULT, DEFAULT, %s, (SELECT id FROM role WHERE name=%s), (SELECT id FROM quota WHERE name=%s)) RETURNING id', (username, fs_uid, auth_source, role, quota))
        self.cursor.execute(query)
        self.sql_manager.commit()
        return self.cursor.fetchone()[0]

    def delete(self, user_id):
        """Delete a user from the state."""
        query = 'DELETE FROM execution WHERE user_id=%s'
        self.cursor.execute(query, (user_id,))
        query = 'DELETE FROM "user" WHERE id = %s'
        self.cursor.execute(query, (user_id,))
        self.sql_manager.commit()
