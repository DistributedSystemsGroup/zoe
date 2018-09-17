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
import functools

import psycopg2

from zoe_lib.state.base import BaseRecord, BaseTable

log = logging.getLogger(__name__)


class Execution(BaseRecord):
    """
    A Zoe execution.

    :type time_submit: datetime.datetime
    :type time_start: datetime.datetime
    :type time_end: datetime.datetime
    """

    SUBMIT_STATUS = "submitted"
    QUEUED_STATUS = "queued"
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
            self.time_submit = datetime.datetime.utcfromtimestamp(d['time_submit'])

        if isinstance(d['time_submit'], datetime.datetime):
            self.time_start = d['time_start']
        else:
            self.time_start = datetime.datetime.utcfromtimestamp(d['time_start'])

        if isinstance(d['time_submit'], datetime.datetime):
            self.time_end = d['time_end']
        else:
            self.time_submit = datetime.datetime.utcfromtimestamp(d['time_start'])

        self._status = d['status']
        self.error_message = d['error_message']

        if d['size'] is not None:
            self.size = float(d['size'])
        else:
            try:
                self.size = self.description['size']
            except KeyError:
                self.size = self.description['priority']  # zapp format v2

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'time_submit': (self.time_submit - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1),
            'time_start': None if self.time_start is None else (self.time_start - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1),
            'time_end': None if self.time_end is None else (self.time_end - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1),
            'status': self._status,
            'error_message': self.error_message,
            'services': [s.id for s in self.services],
            'size': self.size
        }

    def __eq__(self, other):
        return self.id == other.id

    def set_queued(self):
        """The execution has been added to the scheduler queues."""
        self._status = self.QUEUED_STATUS
        self.sql_manager.executions.update(self.id, status=self._status)

    def set_starting(self):
        """The services of the execution are being created in Swarm."""
        self._status = self.STARTING_STATUS
        self.sql_manager.executions.update(self.id, status=self._status)

    def set_running(self):
        """The execution is running and producing useful work."""
        self._status = self.RUNNING_STATUS
        self.time_start = datetime.datetime.utcnow()
        self.sql_manager.executions.update(self.id, status=self._status, time_start=self.time_start)

    def set_cleaning_up(self):
        """The services of the execution are being terminated."""
        self._status = self.CLEANING_UP_STATUS
        self.sql_manager.executions.update(self.id, status=self._status)

    def set_terminated(self, reason=None):
        """The execution is not running."""
        self._status = self.TERMINATED_STATUS
        self.time_end = datetime.datetime.utcnow()
        if reason is not None:
            self.sql_manager.executions.update(self.id, status=self._status, time_end=self.time_end, error_message=reason)
        else:
            self.sql_manager.executions.update(self.id, status=self._status, time_end=self.time_end)

    def set_error(self):
        """The scheduler encountered an error starting or running the execution."""
        self._status = self.ERROR_STATUS
        self.time_end = datetime.datetime.utcnow()
        self.sql_manager.executions.update(self.id, status=self._status, time_end=self.time_end)

    def set_error_message(self, message):
        """Contains an error message in case the status is 'error'."""
        self.error_message = message
        self.sql_manager.executions.update(self.id, error_message=self.error_message)

    def set_size(self, new_size):
        """Changes the size of the execution, for policies that calculate the size automatically."""
        self.size = new_size
        self.sql_manager.executions.update(self.id, size=new_size)

    @property
    def is_active(self):
        """
        Returns False if the execution ended completely
        :return:
        """
        return self._status == self.SUBMIT_STATUS or self._status == self.QUEUED_STATUS or self._status == self.RUNNING_STATUS or self._status == self.STARTING_STATUS or self._status == self.CLEANING_UP_STATUS

    @property
    def is_running(self):
        """Returns True is the execution has at least the essential services running."""
        return self._status == self.RUNNING_STATUS

    @property
    def status(self):
        """Getter for the execution status."""
        return self._status

    @property
    def services(self):
        """Getter for this execution service list."""
        return self.sql_manager.services.select(execution_id=self.id)

    @property
    def essential_services(self):
        """Getter for this execution essential service list."""
        return self.sql_manager.services.select(execution_id=self.id, essential=True)

    @property
    def elastic_services(self):
        """Getter for this execution elastic service list."""
        return self.sql_manager.services.select(execution_id=self.id, essential=False)

    @property
    def essential_services_running(self) -> bool:
        """Returns True if all essential services of this execution have started."""
        for service in self.services:
            if service.essential and service.is_dead():
                return False
        return True

    @property
    def all_services_running(self) -> bool:
        """Return True if all services of this execution are running."""
        for service in self.services:
            if service.is_dead():
                return False
        return True

    @property
    def all_services_active(self) -> bool:
        """Return True if all services of this execution are active."""
        for service in self.services:
            if service.status != service.ACTIVE_STATUS:
                return False
        return True

    @property
    def running_services_count(self) -> int:
        """Returns the number of services of this execution that are running."""
        count = 0
        for service in self.services:
            if not service.is_dead():
                count += 1
        return count

    @property
    def services_count(self) -> int:
        """Return the total number of services defined for this execution."""
        return len(self.services)

    @property
    def total_reservations(self):
        """Return the union/sum of resources reserved by all services of this execution."""
        if len(self.services) == 0:
            return None
        return functools.reduce(lambda x, y: x + y, [s.resource_reservation for s in self.services])

    @property
    def owner(self):
        """Returns the full user object that owns this execution."""
        return self.sql_manager.user.select(only_one=True, **{'id': self.user_id})

    def __repr__(self):
        return str(self.id)


class ExecutionTable(BaseTable):
    """Abstraction for the execution table in the database."""
    def __init__(self, sql_manager):
        super().__init__(sql_manager, "execution")

    def create(self):
        """Create the execution table."""
        self.cursor.execute('''CREATE TABLE execution (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            user_id INT REFERENCES "user",
            description JSON NOT NULL,
            status TEXT NOT NULL,
            size NUMERIC NOT NULL,
            time_submit TIMESTAMP NOT NULL,
            time_start TIMESTAMP NULL,
            time_end TIMESTAMP NULL,
            error_message TEXT NULL
            )''')

    def insert(self, name, user_id, description):
        """Create a new execution in the state."""
        status = Execution.SUBMIT_STATUS
        time_submit = datetime.datetime.utcnow()
        query = self.cursor.mogrify('INSERT INTO execution (id, name, user_id, description, status, size, time_submit) VALUES (DEFAULT, %s,%s,%s,%s,%s,%s) RETURNING id', (name, user_id, description, status, description['size'], time_submit))
        self.cursor.execute(query)
        self.sql_manager.commit()
        return self.cursor.fetchone()[0]

    def select(self, only_one=False, limit=-1, base=0, **kwargs):
        """
        Return a list of executions.

        :param only_one: only one result is expected
        :type only_one: bool
        :param limit: limit the result to this number of entries
        :type limit: int
        :type base: int
        :param base: the base value to use when limiting result count
        :param kwargs: filter executions based on their fields/columns
        :return: one or more executions
        """
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
                q += ' ORDER BY id DESC LIMIT {} OFFSET {}'.format(limit, base)
            query = self.cursor.mogrify(q, args_list)
        else:
            if limit > 0:
                q_base += ' ORDER BY id DESC LIMIT {} OFFSET {}'.format(limit, base)
            query = self.cursor.mogrify(q_base)

        try:
            self.cursor.execute(query)
        except psycopg2.Error as e:
            log.error('db error: {}'.format(e))
            if only_one:
                return None
            else:
                return []

        if only_one:
            row = self.cursor.fetchone()
            if row is None:
                return None
            return Execution(row, self.sql_manager)
        else:
            return [Execution(x, self.sql_manager) for x in self.cursor]

    def count(self, **kwargs):
        """
        Return a list of executions.

        :param kwargs: filter executions based on their fields/columns
        :return: one or more executions
        """
        q_base = 'SELECT COUNT(*) FROM execution'
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
            query = self.cursor.mogrify(q, args_list)
        else:
            query = self.cursor.mogrify(q_base)

        try:
            self.cursor.execute(query)
        except psycopg2.Error as e:
            log.error('db error: {}'.format(e))
            return 0

        row = self.cursor.fetchone()
        return row[0]
