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

import psycopg2
import psycopg2.extras

import zoe_api.exceptions
from zoe_lib.config import get_conf

SQL_SCHEMA_VERSION = 0  # ---> Increment this value every time the schema changes !!! <---


def version_table(cur):
    cur.execute("CREATE TABLE IF NOT EXISTS public.versions (deployment text, version integer)")


def schema(cur, deployment_name):
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = %s)", (deployment_name,))
    if not cur.fetchone()[0]:
        cur.execute('CREATE SCHEMA %s', (deployment_name,))


def check_schema_version(cur, deployment_name):
    cur.execute("SELECT version FROM public.versions WHERE deployment = %s", (deployment_name,))
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO public.versions (deployment, version) VALUES (%s, %s)", (deployment_name, SQL_SCHEMA_VERSION))
        schema(cur, deployment_name)
        return False  # Tables need to be created
    else:
        if row[0] == SQL_SCHEMA_VERSION:
            return True
        else:
            raise zoe_api.exceptions.ZoeException('SQL database schema version mismatch: need {}, found {}'.format(SQL_SCHEMA_VERSION, row[0]))


def create_tables(cur):
    cur.execute('''CREATE TABLE execution (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        user_id TEXT NOT NULL,
        description JSON NOT NULL,
        status TEXT NOT NULL,
        execution_manager_id TEXT NULL,
        time_submit TIMESTAMP NOT NULL,
        time_start TIMESTAMP NULL,
        time_end TIMESTAMP NULL,
        error_message TEXT NULL
        )''')
    cur.execute('''CREATE TABLE service (
        id SERIAL PRIMARY KEY,
        status TEXT NOT NULL,
        error_message TEXT NULL DEFAULT NULL,
        description JSON NOT NULL,
        execution_id INT REFERENCES execution,
        service_group TEXT NOT NULL,
        name TEXT NOT NULL ,
        docker_id TEXT NULL DEFAULT NULL
        )''')


def init():
    dsn = 'dbname=' + get_conf().dbname + \
        ' user=' + get_conf().dbuser + \
        ' password=' + get_conf().dbpass + \
        ' host=' + get_conf().dbhost + \
        ' port=' + str(get_conf().dbport)

    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    version_table(cur)
    cur.execute('SET search_path TO {},public'.format(get_conf().deployment_name))
    if not check_schema_version(cur, get_conf().deployment_name):
        create_tables(cur)

    conn.commit()
    cur.close()
    conn.close()
    return
