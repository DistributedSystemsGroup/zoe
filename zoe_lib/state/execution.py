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
import threading

log = logging.getLogger(__name__)


class Execution:
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
        self.sql_manager = sql_manager
        self.id = d['id']

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

        self.priority = self.description['priority']

        self.termination_lock = threading.Lock()

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

    @property
    def is_active(self):
        """
        Returns True if the execution is in the scheduler
        :return:
        """
        return self._status == self.SCHEDULED_STATUS or self._status == self.RUNNING_STATUS or self._status == self.STARTING_STATUS or self._status == self.CLEANING_UP_STATUS

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
        return self.sql_manager.service_list(execution_id=self.id)

    @property
    def essential_services(self):
        """Getter for this execution essential service list."""
        return self.sql_manager.service_list(execution_id=self.id, essential=True)

    @property
    def elastic_services(self):
        """Getter for this execution elastic service list."""
        return self.sql_manager.service_list(execution_id=self.id, essential=False)

    @property
    def essential_services_running(self) -> bool:
        """Returns True if all essential services of this execution have started."""
        for service in self.services:
            if service.essential and service.is_dead():
                return False
        return True

    @property
    def all_services_running(self) -> bool:
        """Return True if all services of this execution are running/active"""
        for service in self.services:
            if service.is_dead():
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
        return sum([s.resource_reservation for s in self.services])

    def __repr__(self):
        return str(self.id)
