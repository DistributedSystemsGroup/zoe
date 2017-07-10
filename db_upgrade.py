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

"""Database upgrade."""

import sys

import psycopg2
import psycopg2.extras

from zoe_lib.config import get_conf, load_configuration
from zoe_api.db_init import SQL_SCHEMA_VERSION

psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

def _get_schema_version(dsn):
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute('SET search_path TO {},public'.format(get_conf().deployment_name))
    cur.execute("SELECT version FROM public.versions WHERE deployment = %s", (get_conf().deployment_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return None
    return row[0]


def check_schema_version(dsn):
    """Check if the schema version matches this source code version."""
    current_version = _get_schema_version(dsn)
    if current_version is None:
        print('No database schema found for this deployment, use the "create_db_tables.py" script to create one.')
        sys.exit(0)
    else:
        print("Detected schema version {}".format(current_version))
        if current_version < 1:
            print('Schema version {} is too old, cannot upgrade')
            sys.exit(1)
        if current_version == SQL_SCHEMA_VERSION:
            print('DB schema already at latest supported version, no upgrade to perform.')
            sys.exit(1)
        elif current_version < SQL_SCHEMA_VERSION:
            upgrade_schema_from(current_version, dsn)
        else:
            print('SQL database schema version mismatch: need {}, found {}, cannot downgrade'.format(SQL_SCHEMA_VERSION, current_version))
            sys.exit(1)


def upgrade_schema_from(start_version, dsn):
    """Main schema upgrader, calls specific version upgraders as needed"""
    print('Upgrading database from version {} to version {}'.format(start_version, SQL_SCHEMA_VERSION))
    while start_version < SQL_SCHEMA_VERSION:
        new_version = start_version + 1
        UPGRADERS[new_version](dsn)
        start_version = new_version


def upgrade_to_2(dsn):
    """Perform schema upgrade from version 2 to version 3."""
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute('SET search_path TO {},public'.format(get_conf().deployment_name))

    print('Applying schema version 2...')

    cur.execute("UPDATE public.versions SET version = 2 WHERE deployment = %s", (get_conf().deployment_name,))
    conn.commit()
    cur.close()
    conn.close()
    return


def upgrade_to_3(dsn):
    """Perform schema upgrade from version 2 to version 3."""
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute('SET search_path TO {},public'.format(get_conf().deployment_name))

    print('Applying schema version 3...')
    cur.execute("ALTER TABLE service RENAME COLUMN docker_id TO backend_id")
    cur.execute("ALTER TABLE service RENAME COLUMN docker_status TO backend_status")
    cur.execute("ALTER TABLE service ADD ip_address CIDR DEFAULT NULL NULL")
    cur.execute("ALTER TABLE service ADD essential BOOLEAN DEFAULT FALSE NOT NULL")

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

    cur.execute("UPDATE public.versions SET version = 3 WHERE deployment = %s", (get_conf().deployment_name,))
    conn.commit()
    cur.close()
    conn.close()
    return


def upgrade_to_4(dsn):
    """Perform schema upgrade from version 3 to version 4."""
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur.execute('SET search_path TO {},public'.format(get_conf().deployment_name))
    cur2.execute('SET search_path TO {},public'.format(get_conf().deployment_name))

    print('Applying schema version 4...')
    cur.execute('''CREATE TABLE port (
        id SERIAL PRIMARY KEY,
        service_id INT REFERENCES service ON DELETE CASCADE,
        internal_name TEXT NOT NULL,
        external_ip INET NULL,
        external_port INT NULL,
        description JSON NOT NULL
    )''')

    print('Filling the new port table with data from old service descriptions')
    cur.execute("SELECT id, description FROM service")
    for service_id, service_descr in cur:
        for port_descr in service_descr['ports']:
            port_internal = str(port_descr['port_number']) + '/' + port_descr['protocol']

            cur2.execute('INSERT INTO port (id, service_id, internal_name, external_ip, external_port, description) VALUES (DEFAULT, %s, %s, NULL, NULL, %s) RETURNING id', (service_id, port_internal, port_descr))

    cur.execute("UPDATE public.versions SET version = 4 WHERE deployment = %s", (get_conf().deployment_name,))
    conn.commit()
    cur.close()
    cur2.close()
    conn.close()
    return


def upgrade_to_5(dsn):
    """Perform schema upgrade from version 4 to version 5."""
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur2 = conn.cursor()
    cur.execute('SET search_path TO {},public'.format(get_conf().deployment_name))
    cur2.execute('SET search_path TO {},public'.format(get_conf().deployment_name))

    print('Applying schema version 5...')
    print('-> changing type of service id to BIGINT')
    cur.execute("ALTER TABLE service ALTER COLUMN id TYPE BIGINT")
    print('-> changing type of execution id to BIGINT')
    cur.execute("ALTER TABLE execution ALTER COLUMN id TYPE BIGINT")

    print('-> create table quotas')
    cur.execute('''CREATE TABLE quotas (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        concurrent_executions INT NOT NULL,
        memory BIGINT NOT NULL,
        cores INT NOT NULL
    )''')
    print('-> create default quota')
    cur.execute('''INSERT INTO quotas (id, name, concurrent_executions, memory, cores) VALUES (DEFAULT, 'default', 5, 34359738368, 20)''')
    print('-> create table users')
    cur.execute('''CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        priority SMALLINT NOT NULL DEFAULT 0,
        enabled BOOLEAN NOT NULL DEFAULT TRUE,
        quota_id INT REFERENCES quotas
    )''')
    cur.execute('CREATE UNIQUE INDEX users_username_uindex ON users (username)')

    print('Filling the user table from the execution data...')
    print('-> The default quota will be assigned to all users')
    cur.execute("SELECT user_id FROM execution")
    users = set([u[0] for u in cur])
    for user_name in users:
        cur2.execute("INSERT INTO users (id, username, role, email, priority, enabled, quota_id) VALUES (DEFAULT, %s, 'user', NULL, DEFAULT, DEFAULT, currval('quotas_id_seq'))", (user_name, ))
        cur2.execute("UPDATE execution SET user_id=currval('users_id_seq') WHERE user_id=%s", (user_name, ))

    print('-> change type of user_id to INT')
    cur.execute("ALTER TABLE execution ALTER COLUMN user_id TYPE INT USING CAST(user_id AS INT)")
    print('-> create foreign key for executions.user_id pointing to users.id')
    cur.execute('ALTER TABLE execution ADD CONSTRAINT execution_user_id_fk FOREIGN KEY (user_id) REFERENCES users (id)')

    print('-> converting oauth tables')
    cur.execute('DROP TABLE oauth_client')
    cur.execute('DROP TABLE oauth_token')

    cur.execute("UPDATE public.versions SET version = 5 WHERE deployment = %s", (get_conf().deployment_name,))
    conn.commit()
    cur.close()
    cur2.close()
    conn.close()
    return


UPGRADERS = [
    None,
    None,
    upgrade_to_2,
    upgrade_to_3,
    upgrade_to_4,
    upgrade_to_5
]


def init():
    """DB upgrade entrypoint."""
    load_configuration()

    dsn = 'dbname=' + get_conf().dbname + \
        ' user=' + get_conf().dbuser + \
        ' password=' + get_conf().dbpass + \
        ' host=' + get_conf().dbhost + \
        ' port=' + str(get_conf().dbport)

    check_schema_version(dsn)

    return

if __name__ == "__main__":
    init()
