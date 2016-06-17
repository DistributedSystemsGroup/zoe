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

import datetime

import psycopg2
import psycopg2.extras
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)


class SQLManager:
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
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SET search_path TO {},public'.format(self.schema))
        return cur

    def execution_list(self, only_one=False, **kwargs):
        cur = self._cursor()
        q_base = 'SELECT * FROM execution'
        if len(kwargs) > 0:
            q = q_base + " WHERE "
            filter_list = []
            args_list = []
            for k, v in kwargs.items():
                filter_list.append('{} = %s'.format(k))
                args_list.append(v)
            q += ', '.join(filter_list)
            query = cur.mogrify(q, args_list)
        else:
            query = cur.mogrify(q_base)

        cur.execute(query)
        if only_one:
            return Execution(cur.fetchone(), self)
        else:
            return [Execution(x, self) for x in cur]

    def execution_update(self, exec_id, **kwargs):
        cur = self._cursor()
        arg_list = []
        value_list = []
        for k, v in kwargs.items():
            arg_list.append('{} = %s'.format(k))
            value_list.append(v)
        set_q = ", ".join(arg_list)
        value_list.append(exec_id)
        q_base = 'UPDATE execution SET' + set_q + ' WHERE id=%s'
        query = cur.mogrify(q_base, value_list)
        cur.execute(query)
        self.conn.commit()

    def execution_new(self, name, user_id, description):
        cur = self._cursor()
        status = 'submitted'
        time_submit = datetime.datetime.now()
        query = cur.mogrify('INSERT INTO execution (id, name, user_id, description, status, time_submit) VALUES (DEFAULT, %s,%s,%s,%s,%s) RETURNING id', (name, user_id, description, status, time_submit))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()


class Base:
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
        raise NotImplementedError


class Execution(Base):
    """
    :type time_submit: datetime.datetime
    :type time_start: datetime.datetime
    :type time_end: datetime.datetime
    """
    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.user_id = d['user_id']
        self.name = d['name']
        self.description = d['description']

        if isinstance(d['time_submit'], datetime.datetime):
            self.time_submit = d['time_submit']
        else:
            self.time_submit = datetime.datetime.fromtimestamp(d['time_submit'])

        if isinstance(d['time_submit'], datetime.datetime):
            self.time_start = d['time_start']
        else:
            self.time_start = datetime.datetime.fromtimestamp(d['time_start'])

        if isinstance(d['time_submit'], datetime.datetime):
            self.time_end = d['time_end']
        else:
            self.time_submit = datetime.datetime.fromtimestamp(d['time_start'])

        self.status = d['status']
        self.error_message = d['error_message']

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'time_submit': self.time_submit.timestamp(),
            'time_start': None if self.time_start is None else self.time_start.timestamp(),
            'time_end': None if self.time_end is None else self.time_end.timestamp(),
            'status': self.status,
            'error_message': self.error_message
        }

    def set_scheduled(self):
        self.status = "scheduled"
        self.sql_manager.execution_update(self.id, status=self.status)

    def set_started(self):
        self.status = "running"
        self.time_start = datetime.datetime.now()
        self.sql_manager.execution_update(self.id, status=self.status, time_start=self.time_start)

    def set_finished(self):
        self.status = "finished"
        self.time_end = datetime.datetime.now()
        self.sql_manager.execution_update(self.id, status=self.status, time_end=self.time_end)

    def set_cleaning_up(self):
        self.status = "cleaning up"
        self.sql_manager.execution_update(self.id, status=self.status)

    def set_terminated(self):
        self.status = "terminated"
        self.time_end = datetime.datetime.now()
        self.sql_manager.execution_update(self.id, status=self.status, time_end=self.time_end)

    def set_error(self, message):
        self.status = 'error'
        self.error_message = message
        self.time_end = datetime.datetime.now()
        self.sql_manager.execution_update(self.id, status=self.status, time_end=self.time_end, error_message=self.error_message)

    def is_active(self):
        return self.status == 'scheduled' or self.status == 'running'
