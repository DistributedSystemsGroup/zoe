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

        self.name = d['name']
        self.concurrent_executions = d['concurrent_executions']
        self.memory = d['memory']
        self.cores = d['cores']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'concurrent_executions': self.concurrent_executions,
            'cores': self.cores,
            'memory': self.memory
        }

    def set_concurrent_executions(self, value):
        """Setter for concurrent execution limit."""
        self.concurrent_executions = value
        self.sql_manager.quota_update(self.id, concurrent_executions=value)

    def set_memory(self, value):
        """Setter for memory limit."""
        self.memory = value
        self.sql_manager.quota_update(self.id, memory=value)

    def set_cores(self, value):
        """Setter for cores limit."""
        self.cores = value
        self.sql_manager.quota_update(self.id, cores=value)
