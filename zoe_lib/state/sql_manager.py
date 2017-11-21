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

import psycopg2
import psycopg2.extras

from .service import ServiceTable
from .execution import ExecutionTable
from .port import PortTable

from zoe_lib.config import get_conf
from zoe_lib.version import SQL_SCHEMA_VERSION
import zoe_lib.exceptions

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

    @property
    def executions(self) -> ExecutionTable:
        """Access the execution state."""
        cur = self._cursor()
        return ExecutionTable(self.conn, cur)

    @property
    def services(self) -> ServiceTable:
        """Access the service state."""
        cur = self._cursor()
        return ServiceTable(self.conn, cur)

    @property
    def ports(self) -> PortTable:
        """Access the port state."""
        cur = self._cursor()
        return PortTable(self.conn, cur)

    def _create_tables(self):
        self.executions.create()
        self.services.create()
        self.ports.create()

    def init_db(self, force=False):
        """DB init entrypoint."""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("CREATE TABLE IF NOT EXISTS public.versions (deployment text, version integer)")

        cur.execute('SET search_path TO {},public'.format(get_conf().deployment_name))

        if force:
            cur.execute("DELETE FROM public.versions WHERE deployment = %s", (get_conf().deployment_name,))
            cur.execute('DROP SCHEMA IF EXISTS {} CASCADE'.format(get_conf().deployment_name))

        if not self._check_schema_version(cur, get_conf().deployment_name):
            self._create_tables()

        self.conn.commit()
        cur.close()

    def _check_schema_version(self, cur, deployment_name):
        """Check if the schema version matches this source code version."""
        cur.execute("SELECT version FROM public.versions WHERE deployment = %s", (deployment_name,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO public.versions (deployment, version) VALUES (%s, %s)", (deployment_name, SQL_SCHEMA_VERSION))
            cur.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = %s)", (deployment_name,))
            if not cur.fetchone()[0]:
                cur.execute('CREATE SCHEMA {}'.format(deployment_name))
            return False  # Tables need to be created
        else:
            if row[0] == SQL_SCHEMA_VERSION:
                return True
            else:
                raise zoe_lib.exceptions.ZoeLibException('SQL database schema version mismatch: need {}, found {}'.format(SQL_SCHEMA_VERSION, row[0]))
