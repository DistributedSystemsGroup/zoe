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

"""Interface to PostgresQL for Zoe state."""

import datetime
import logging

import psycopg2
import psycopg2.extras

from zoe_lib.config import get_conf
from zoe_lib.swarm_client import SwarmClient

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

    def service_new(self, execution_id, name, service_group, description):
        """Adds a new service to the state."""
        cur = self._cursor()
        status = 'created'
        query = cur.mogrify('INSERT INTO service (id, status, error_message, execution_id, name, service_group, description) VALUES (DEFAULT, %s,NULL,%s,%s,%s,%s) RETURNING id', (status, execution_id, name, service_group, description))
        cur.execute(query)
        self.conn.commit()
        return cur.fetchone()[0]


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
        """Generates a dictionary that can be serialized in JSON."""
        raise NotImplementedError


class Execution(Base):
    """
    A Zoe execution.

    :type time_submit: datetime.datetime
    :type time_start: datetime.datetime
    :type time_end: datetime.datetime
    """

    SUBMIT_STATUS = "submitted"
    SCHEDULED_STATUS = "scheduled"
    STARTING_STATUS = "starting"
    ERROR_STATUS = "error"
    RUNNING_STATUS = "running"
    CLEANING_UP_STATUS = "cleaning up"
    TERMINATED_STATUS = "terminated"

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

        self._status = d['status']
        self.error_message = d['error_message']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'time_submit': self.time_submit.timestamp(),
            'time_start': None if self.time_start is None else self.time_start.timestamp(),
            'time_end': None if self.time_end is None else self.time_end.timestamp(),
            'status': self._status,
            'error_message': self.error_message,
            'services': [s.id for s in self.services]
        }

    def __eq__(self, other):
        return self.id == other.id

    def set_scheduled(self):
        """The execution has been added to the scheduler queues."""
        self._status = self.SCHEDULED_STATUS
        self.sql_manager.execution_update(self.id, status=self._status)

    def set_starting(self):
        """The services of the execution are being created in Swarm."""
        self._status = self.STARTING_STATUS
        self.sql_manager.execution_update(self.id, status=self._status)

    def set_running(self):
        """The execution is running and producing useful work."""
        self._status = self.RUNNING_STATUS
        self.time_start = datetime.datetime.now()
        self.sql_manager.execution_update(self.id, status=self._status, time_start=self.time_start)

    def set_cleaning_up(self):
        """The services of the execution are being terminated."""
        self._status = self.CLEANING_UP_STATUS
        self.sql_manager.execution_update(self.id, status=self._status)

    def set_terminated(self):
        """The execution is not running."""
        self._status = self.TERMINATED_STATUS
        self.time_end = datetime.datetime.now()
        self.sql_manager.execution_update(self.id, status=self._status, time_end=self.time_end)

    def set_error(self):
        """The scheduler encountered an error starting or running the execution."""
        self._status = self.ERROR_STATUS
        self.time_end = datetime.datetime.now()
        self.sql_manager.execution_update(self.id, status=self._status, time_end=self.time_end)

    def set_error_message(self, message):
        """Contains an error message in case the status is 'error'."""
        self.error_message = message
        self.sql_manager.execution_update(self.id, error_message=self.error_message)

    def is_active(self):
        """
        Returns True if the execution is in the scheduler
        :return:
        """
        return self._status == self.SCHEDULED_STATUS or self._status == self.RUNNING_STATUS or self._status == self.STARTING_STATUS or self._status == self.CLEANING_UP_STATUS

    @property
    def status(self):
        """Getter for the execution status."""
        return self._status

    @property
    def services(self):
        """Getter for this execution service list."""
        return self.sql_manager.service_list(execution_id=self.id)


class Service(Base):
    """A Zoe Service."""

    TERMINATING_STATUS = "terminating"
    INACTIVE_STATUS = "inactive"
    ACTIVE_STATUS = "active"
    STARTING_STATUS = "starting"
    ERROR_STATUS = "error"

    DOCKER_UNDEFINED_STATUS = 'undefined'
    DOCKER_CREATE_STATUS = 'created'
    DOCKER_START_STATUS = 'started'
    DOCKER_DIE_STATUS = 'dead'
    DOCKER_DESTROY_STATUS = 'destroyed'
    DOCKER_OOM_STATUS = 'oom-killed'

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.name = d['name']
        self.status = d['status']
        self.error_message = d['error_message']
        self.execution_id = d['execution_id']
        self.description = d['description']
        self.service_group = d['service_group']
        self.docker_id = d['docker_id']
        self.docker_status = d['docker_status']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'error_message': self.error_message,
            'execution_id': self.execution_id,
            'description': self.description,
            'service_group': self.service_group,
            'docker_id': self.docker_id,
            'ip_address': self.ip_address,
            'docker_status': self.docker_status
        }

    def __eq__(self, other):
        return self.id == other.id

    @property
    def dns_name(self):
        """Getter for the DNS name of this service as it will be registered in Docker's DNS."""
        return "{}-{}-{}".format(self.name, self.execution_id, get_conf().deployment_name)

    def set_terminating(self):
        """The service is being killed."""
        self.sql_manager.service_update(self.id, status=self.TERMINATING_STATUS)
        self.status = self.TERMINATING_STATUS

    def set_inactive(self):
        """The service is not running."""
        self.sql_manager.service_update(self.id, status=self.INACTIVE_STATUS, docker_id=None)
        self.status = self.INACTIVE_STATUS

    def set_starting(self):
        """The service is being created by Docker."""
        self.sql_manager.service_update(self.id, status=self.STARTING_STATUS)
        self.status = self.STARTING_STATUS

    def set_active(self, docker_id):
        """The service is running and has a valid docker_id."""
        self.sql_manager.service_update(self.id, status=self.ACTIVE_STATUS, docker_id=docker_id, error_message=None)
        self.error_message = None
        self.status = self.ACTIVE_STATUS

    def set_error(self, error_message):
        """The service could not be created/started."""
        self.sql_manager.service_update(self.id, status=self.ERROR_STATUS, error_message=error_message)
        self.status = self.ERROR_STATUS
        self.error_message = error_message

    def set_docker_status(self, new_status):
        """Docker has emitted an event related to this service."""
        self.sql_manager.service_update(self.id, docker_status=new_status)
        log.debug("service {}, status updated to {}".format(self.id, new_status))
        self.docker_status = new_status

    @property
    def ip_address(self):
        """Getter for the service IP address, queries Swarm as the IP address changes outside our control."""
        if self.docker_status != self.DOCKER_START_STATUS:
            return {}
        swarm = SwarmClient(get_conf())
        s_info = swarm.inspect_container(self.docker_id)
        return s_info['ip_address'][get_conf().overlay_network_name]

    @property
    def ports(self):
        """Getter for the port mappings created by Swarm."""
        if self.docker_status != self.DOCKER_START_STATUS:
            return {}
        swarm = SwarmClient(get_conf())
        s_info = swarm.inspect_container(self.docker_id)
        return s_info['ports']

    @property
    def user_id(self):
        """Getter for the user_id, that is actually taken form the parent execution."""
        execution = self.sql_manager.execution_list(only_one=True, id=self.execution_id)
        return execution.user_id
