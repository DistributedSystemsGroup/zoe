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

"""Database initialization."""

import psycopg2
import psycopg2.extras

import zoe_api.exceptions
from zoe_lib.config import get_conf

SQL_SCHEMA_VERSION = 3  # ---> Increment this value every time the schema changes !!! <---


def version_table(cur):
    """Create the version table."""
    cur.execute("CREATE TABLE IF NOT EXISTS public.versions (deployment text, version integer)")


def schema(cur, deployment_name):
    """Create the schema for the configured deployment name."""
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname = %s)", (deployment_name,))
    if not cur.fetchone()[0]:
        cur.execute('CREATE SCHEMA {}'.format(deployment_name))


def check_schema_version(cur, deployment_name):
    """Check if the schema version matches this source code version."""
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
    """Create the Zoe database tables."""
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
        name TEXT NOT NULL,
        backend_id TEXT NULL DEFAULT NULL,
        backend_status TEXT NOT NULL DEFAULT 'undefined',
        ip_address CIDR NULL DEFAULT NULL,
        essential BOOLEAN NOT NULL DEFAULT FALSE
        )''')
    #Create oauth_client and oauth_token tables for oAuth2
    cur.execute('''CREATE TABLE oauth_client (
        identifier TEXT PRIMARY KEY,
        secret TEXT,
        role TEXT,
        redirect_uris TEXT,
        authorized_grants TEXT,
        authorized_response_types TEXT
        )''')
    cur.execute('''CREATE TABLE oauth_token (
        client_id TEXT PRIMARY KEY,
        grant_type TEXT,
        token TEXT,
        data TEXT,
        expires_at TIMESTAMP,
        refresh_token TEXT,
        refresh_token_expires_at TIMESTAMP,
        scopes TEXT,
        user_id TEXT
        )''')


def init():
    """DB init entrypoint."""
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
