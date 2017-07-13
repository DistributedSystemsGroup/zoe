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

import datetime
import logging

import psycopg2
import psycopg2.extras

from .service import Service
from .execution import Execution
from .port import Port
from .quota import Quota
from .user import User

log = logging.getLogger(__name__)

psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)


class SQLManager:
    """The SQLManager class, should be used as a singleton."""
    def __init__(self, conf):
        self.user = conf.dbuser
        self.password = conf.dbpass
        self.host = conf.dbhost
        self.port = conf.dbport
        self.dbname = conf.dbname
        self.schema = conf.deployment_name
        self.conn = None
        self._connect()

    def _connect(self):
        dsn = 'dbname=' + self.dbname + \
              ' user=' + self.user + \
              ' password=' + self.password + \
              ' host=' + self.host + \
              ' port=' + str(self.port)

        self.conn = psycopg2.connect(dsn)

    def _cursor(self):
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except psycopg2.InterfaceError:
            self._connect()
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SET search_path TO {},public'.format(self.schema))
        return cur

    def execution_list(self, only_one=False, limit=-1, **kwargs):
        """
        Return a list of executions.

        :param only_one: only one result is expected
        :type only_one: bool
        :param limit: limit the result to this number of entries
        :type limit: int
        :param kwargs: filter executions based on their fields/columns
        :return: one or more executions
        """
        cur = self._cursor()
        q_base = 'SELECT * FROM execution'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for key, value in kwargs.items():
                if key == 'earlier_than_submit':
                    filter_list.append('"time_submit" <= to_timestamp(%s)')
                elif key == 'earlier_than_start':
                    filter_list.append('"time_start" <= to_timestamp(%s)')
                elif key == 'earlier_than_end':
                    filter_list.append('"time_end" <= to_timestamp(%s)')
                elif key == 'later_than_submit':
                    filter_list.append('"time_submit" >= to_timestamp(%s)')
                elif key == 'later_than_start':
                    filter_list.append('"time_start" >= to_timestamp(%s)')
                elif key == 'later_than_end':
                    filter_list.append('"time_end" >= to_timestamp(%s)')
                else:
                    filter_list.append('{} = %s'.format(key))
                args_list.append(value)
            q += ' AND '.join(filter_list)
            if limit > 0:
                q += ' ORDER BY id DESC LIMIT {}'.format(limit)
            query = cur.mogrify(q, args_list)
        else:
            if limit > 0:
                q_base += ' ORDER BY id DESC LIMIT {}'.format(limit)
            query = cur.mogrify(q_base)

        cur.execute(query)
        if only_one:
            row = cur.fetchone()
            if row is None:
                return None
            return Execution(row, self)
        else:
            return [Execution(x, self) for x in cur]

    def execution_update(self, exec_id, **kwargs):
        """Update the state of an execution."""
        cur = self._cursor()
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(exec_id)
        q_base = 'UPDATE execution SET ' + set_q + ' WHERE id=%s'
        query = cur.mogrify(q_base, value_list)
        cur.execute(query)
        self.conn.commit()

    def execution_new(self, name, user, description):
        """Create a new execution in the state."""
        cur = self._cursor()
        status = Execution.SUBMIT_STATUS
        time_submit = datetime.datetime.now()
        query = cur.mogrify('INSERT INTO execution (id, name, user_id, description, status, time_submit) VALUES (DEFAULT, %s,%s,%s,%s,%s) RETURNING id', (name, user.id, description, status, time_submit))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]

    def execution_delete(self, execution_id):
        """Delete an execution and its services from the state."""
        cur = self._cursor()
        query = "DELETE FROM execution WHERE id = %s"
        cur.execute(query, (execution_id,))
        self.conn.commit()

    def service_list(self, only_one=False, **kwargs):
        """
        Return a list of services.

        :param only_one: only one result is expected
        :type only_one: bool
        :param kwargs: filter services based on their fields/columns
        :return: one or more services
        """
        cur = self._cursor()
        q_base = 'SELECT * FROM service'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for key, value in kwargs.items():
                filter_list.append('{} = %s'.format(key))
                args_list.append(value)
            q += ' AND '.join(filter_list)
            query = cur.mogrify(q, args_list)
        else:
            query = cur.mogrify(q_base)

        cur.execute(query)
        if only_one:
            row = cur.fetchone()
            if row is None:
                return None
            return Service(row, self)
        else:
            return [Service(x, self) for x in cur]

    def service_update(self, service_id, **kwargs):
        """Update the state of an existing service."""
        cur = self._cursor()
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(service_id)
        q_base = 'UPDATE service SET ' + set_q + ' WHERE id=%s'
        query = cur.mogrify(q_base, value_list)
        cur.execute(query)
        self.conn.commit()

    def service_new(self, execution_id, name, service_group, description, is_essential):
        """Adds a new service to the state."""
        cur = self._cursor()
        status = 'created'
        query = cur.mogrify('INSERT INTO service (id, status, error_message, execution_id, name, service_group, description, essential) VALUES (DEFAULT, %s,NULL,%s,%s,%s,%s,%s) RETURNING id', (status, execution_id, name, service_group, description, is_essential))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]

    def port_list(self, only_one=False, **kwargs):
        """
        Return a list of ports.

        :param only_one: only one result is expected
        :type only_one: bool
        :param kwargs: filter services based on their fields/columns
        :return: one or more ports
        """
        cur = self._cursor()
        q_base = 'SELECT * FROM port'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for key, value in kwargs.items():
                filter_list.append('{} = %s'.format(key))
                args_list.append(value)
            q += ' AND '.join(filter_list)
            query = cur.mogrify(q, args_list)
        else:
            query = cur.mogrify(q_base)

        cur.execute(query)
        if only_one:
            row = cur.fetchone()
            if row is None:
                return None
            return Port(row, self)
        else:
            return [Port(x, self) for x in cur]

    def port_update(self, port_id, **kwargs):
        """Update the state of an existing port."""
        cur = self._cursor()
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(port_id)
        q_base = 'UPDATE port SET ' + set_q + ' WHERE id=%s'
        query = cur.mogrify(q_base, value_list)
        cur.execute(query)
        self.conn.commit()

    def port_new(self, service_id, internal_name, description):
        """Adds a new port to the state."""
        cur = self._cursor()
        query = cur.mogrify('INSERT INTO port (id, service_id, internal_name, external_ip, external_port, description) VALUES (DEFAULT, %s, %s, NULL, NULL, %s) RETURNING id', (service_id, internal_name, description))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]

    def quota_list(self, only_one=False, **kwargs):
        """
        Return a list of ports.

        :param only_one: only one result is expected
        :type only_one: bool
        :param kwargs: filter services based on their fields/columns
        :return: one or more ports
        """
        cur = self._cursor()
        q_base = 'SELECT * FROM quotas'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for key, value in kwargs.items():
                filter_list.append('{} = %s'.format(key))
                args_list.append(value)
            q += ' AND '.join(filter_list)
            query = cur.mogrify(q, args_list)
        else:
            query = cur.mogrify(q_base)

        cur.execute(query)
        if only_one:
            row = cur.fetchone()
            if row is None:
                return None
            return Quota(row, self)
        else:
            return [Quota(x, self) for x in cur]

    def quota_update(self, port_id, **kwargs):
        """Update the state of an existing port."""
        cur = self._cursor()
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(port_id)
        q_base = 'UPDATE quotas SET ' + set_q + ' WHERE id=%s'
        query = cur.mogrify(q_base, value_list)
        cur.execute(query)
        self.conn.commit()

    def quota_new(self, name, concurrent_executions, memory, cores):
        """Adds a new port to the state."""
        cur = self._cursor()
        query = cur.mogrify('INSERT INTO quotas (id, name, concurrent_executions, memory, cores) VALUES (DEFAULT, %s, %s, %s, %s) RETURNING id', (name, concurrent_executions, memory, cores))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]

    def quota_delete(self, quota_id):
        """Delete an execution and its services from the state."""
        cur = self._cursor()
        query = "UPDATE users SET quota_id = (SELECT id from quotas WHERE name='default') WHERE quota_id=%s"
        cur.execute(query, (quota_id,))
        query = "DELETE FROM quotas WHERE id = %s"
        cur.execute(query, (quota_id,))
        self.conn.commit()

    def user_list(self, only_one=False, **kwargs):
        """
        Return a list of ports.

        :param only_one: only one result is expected
        :type only_one: bool
        :param kwargs: filter services based on their fields/columns
        :return: one or more ports
        """
        cur = self._cursor()
        q_base = 'SELECT * FROM users'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for key, value in kwargs.items():
                filter_list.append('{} = %s'.format(key))
                args_list.append(value)
            q += ' AND '.join(filter_list)
            query = cur.mogrify(q, args_list)
        else:
            query = cur.mogrify(q_base)

        cur.execute(query)
        if only_one:
            row = cur.fetchone()
            if row is None:
                return None
            return User(row, self)
        else:
            return [User(x, self) for x in cur]

    def user_update(self, port_id, **kwargs):
        """Update the state of an existing port."""
        cur = self._cursor()
        arg_list = []
        value_list = []
        for key, value in kwargs.items():
            arg_list.append('{} = %s'.format(key))
            value_list.append(value)
        set_q = ", ".join(arg_list)
        value_list.append(port_id)
        q_base = 'UPDATE users SET ' + set_q + ' WHERE id=%s'
        query = cur.mogrify(q_base, value_list)
        cur.execute(query)
        self.conn.commit()

    def user_new(self, username, role):
        """Adds a new port to the state."""
        cur = self._cursor()
        query = cur.mogrify('INSERT INTO users (id, username, role, email, priority, enabled, quota_id) VALUES (DEFAULT, %s, %s, NULL, DEFAULT, DEFAULT, (SELECT id FROM quotas WHERE name=\'default\')) RETURNING id', (username, role))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]
