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

    def execution_list(self, only_one=False, **kwargs):
        """
        Return a list of executions.

        :param only_one: only one result is expected
        :type only_one: bool
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

    def execution_new(self, name, user_id, description):
        """Create a new execution in the state."""
        cur = self._cursor()
        status = Execution.SUBMIT_STATUS
        time_submit = datetime.datetime.now()
        query = cur.mogrify('INSERT INTO execution (id, name, user_id, description, status, time_submit) VALUES (DEFAULT, %s,%s,%s,%s,%s) RETURNING id', (name, user_id, description, status, time_submit))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]

    def execution_delete(self, execution_id):
        """Delete an execution and its services from the state."""
        cur = self._cursor()
        query = "DELETE FROM service WHERE execution_id = %s"
        cur.execute(query, (execution_id,))
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

    #The above section is used for Oauth2 authentication mechanism

    def fetch_by_refresh_token(self, refresh_token):
        """ get info from refreshtoken """
        cur = self._cursor()
        query = 'SELECT * FROM oauth_token WHERE refresh_token = %s'
        cur.execute(query, (refresh_token,))

        return cur.fetchone()

    def delete_refresh_token(self, refresh_token):
        """ delete info by refreshtoken """
        cur = self._cursor()
        check_exists = 'SELECT * FROM oauth_token WHERE refresh_token = %s OR token = %s'
        cur.execute(check_exists, (refresh_token, refresh_token))
        res = 0
        if cur.fetchone():
            res = 1
        query = 'DELETE FROM oauth_token WHERE refresh_token = %s OR token = %s'
        cur.execute(query, (refresh_token, refresh_token))
        self.conn.commit()
        return res

    def fetch_existing_token_of_user(self, client_id, grant_type, user_id):
        """ get info from clientid granttype userid """
        cur = self._cursor()
        query = 'SELECT * FROM oauth_token WHERE client_id = %s AND grant_type = %s AND user_id = %s'
        cur.execute(query, (client_id, grant_type, user_id,))

        return cur.fetchone()

    def get_client_id_by_access_token(self, access_token):
        """ get clientid from accesstoken """
        cur = self._cursor()
        query = 'SELECT * FROM oauth_token WHERE token = %s'
        cur.execute(query, (access_token,))

        return cur.fetchone()

    def get_client_id_by_refresh_token(self, refresh_token):
        """ get clientid from refreshtoken """
        cur = self._cursor()
        query = 'SELECT * FROM oauth_token WHERE refresh_token = %s'
        cur.execute(query, (refresh_token,))

        return cur.fetchone()

    def save_token(self, client_id, grant_type, token, data, expires_at, refresh_token, refresh_expires_at, scopes, user_id): #pylint: disable=too-many-arguments
        """ save token to db """
        cur = self._cursor()
        expires_at = datetime.datetime.fromtimestamp(expires_at)
        if refresh_expires_at is None:
            query = cur.mogrify('UPDATE oauth_token SET token = %s, expires_at = %s WHERE client_id=%s', (token, expires_at, client_id))
        else:
            refresh_token_expires_at = datetime.datetime.fromtimestamp(refresh_expires_at)
            query = cur.mogrify('INSERT INTO oauth_token (client_id, grant_type, token, data, expires_at, refresh_token, refresh_token_expires_at, scopes, user_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (client_id) DO UPDATE SET token = %s, expires_at = %s, refresh_token = %s, refresh_token_expires_at = %s', (client_id, grant_type, token, data, expires_at, refresh_token, refresh_token_expires_at, scopes, user_id, token, expires_at, refresh_token, refresh_token_expires_at))

        cur.execute(query)
        self.conn.commit()

    def save_client(self, identifier, secret, role, redirect_uris, authorized_grants, authorized_response_types):
        """ save clientinfo to db """
        cur = self._cursor()
        query = cur.mogrify('INSERT INTO oauth_client (identifier, secret, role, redirect_uris, authorized_grants, authorized_response_types) VALUES (%s,%s,%s,%s,%s,%s)', (identifier, secret, role, redirect_uris, authorized_grants, authorized_response_types))
        cur.execute(query)
        self.conn.commit()

    def fetch_by_client_id(self, client_id):
        """ get info from clientid """
        cur = self._cursor()
        query = 'SELECT * FROM oauth_client WHERE identifier = %s'
        cur.execute(query, (client_id,))

        return cur.fetchone()
