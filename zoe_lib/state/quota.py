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

from zoe_lib.state.base import Base

log = logging.getLogger(__name__)


class Quota(Base):
    """A quota object describes limits imposed to users on resource usage."""

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self._name = d['name']
        self._concurrent_executions = d['concurrent_executions']
        self._memory = d['memory']
        self._cores = d['cores']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'name': self._name,
            'concurrent_executions': self._concurrent_executions,
            'cores': self._cores,
        }

    @property
    def name(self):
        """Getter for the name property."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.sql_manager.quota_update(self.id, name=value)

    @property
    def concurrent_executions(self):
        """Getter for concurrent executions limit."""
        return self._concurrent_executions

    @concurrent_executions.setter
    def concurrent_executions(self, value):
        """Setter for concurrent execution limit."""
        self._concurrent_executions = value
        self.sql_manager.quota_update(self.id, concurrent_executions=value)

    @property
    def memory(self):
        """Getter for memory limit."""
        return self._memory

    @memory.setter
    def memory(self, value):
        """Setter for memory limit."""
        self._memory = value
        self.sql_manager.quota_update(self.id, memory=value)

    @property
    def cores(self):
        """Getter for cores limit."""
        return self._cores

    @cores.setter
    def cores(self, value):
        """Setter for cores limit."""
        self._cores = value
        self.sql_manager.quota_update(self.id, cores=value)