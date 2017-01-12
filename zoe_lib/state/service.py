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

import logging

from zoe_lib.config import get_conf
from zoe_lib.swarm_client import SwarmClient

log = logging.getLogger(__name__)


class ResourceReservation:
    """The resources reserved by a Service."""
    def __init__(self, data):
        self.memory = data['memory']
        self.cores = data['cores']


class VolumeDescription:
    """A generic description for container volumes."""
    def __init__(self, data):
        self.type = "host_directory"
        self.path = data[0]
        self.mount_point = data[1]
        self.readonly = data[2]


class ExposedPort:
    """A port on the container that should be exposed."""
    def __init__(self, data):
        self.proto = 'tcp'  # FIXME UDP ports?
        self.number = data['port_number']
        self.expose = data['expose'] if 'expose' in data else False


class Service:
    """A Zoe Service."""

    TERMINATING_STATUS = "terminating"
    INACTIVE_STATUS = "inactive"
    ACTIVE_STATUS = "active"
    STARTING_STATUS = "starting"
    ERROR_STATUS = "error"

    BACKEND_UNDEFINED_STATUS = 'undefined'
    BACKEND_CREATE_STATUS = 'created'
    BACKEND_START_STATUS = 'started'
    BACKEND_DIE_STATUS = 'dead'
    BACKEND_DESTROY_STATUS = 'destroyed'
    BACKEND_OOM_STATUS = 'oom-killed'

    def __init__(self, d, sql_manager):
        self.sql_manager = sql_manager
        self.id = d['id']

        self.name = d['name']
        self.status = d['status']
        self.error_message = d['error_message']
        self.execution_id = d['execution_id']
        self.description = d['description']
        self.service_group = d['service_group']
        self.backend_id = d['backend_id']
        self.backend_status = d['backend_status']

        # Fields parsed from the JSON description
        self.image_name = self.description['docker_image']
        self.is_monitor = self.description['monitor']
        self.startup_order = self.description['startup_order']
        self.environment = []
        if 'environment' in self.description:
            self.environment = self.description['environment']
        self.command = ''
        if 'command' in self.description:
            self.command = self.description['command']
        self.resource_reservation = ResourceReservation(self.description['required_resources'])
        self.volumes = []
        if 'volumes' in self.description:
            self.volumes = [VolumeDescription(v) for v in self.description['volumes']]
        self.ports = [ExposedPort(p) for p in self.description['ports']]

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
            'backend_id': self.backend_id,
            'ip_address': self.ip_address,
            'backend_status': self.backend_status
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

    def set_backend_status(self, new_status):
        """Docker has emitted an event related to this service."""
        self.sql_manager.service_update(self.id, backend_status=new_status)
        log.debug("service {}, backend status updated to {}".format(self.id, new_status))
        self.docker_status = new_status

    @property
    def ip_address(self):
        """Getter for the service IP address, queries Swarm as the IP address changes outside our control."""
        if self.docker_status != self.BACKEND_START_STATUS:
            return {}
        swarm = SwarmClient(get_conf())
        s_info = swarm.inspect_container(self.backend_id)
        return s_info['ip_address'][get_conf().overlay_network_name]

    @property
    def user_id(self):
        """Getter for the user_id, that is actually taken form the parent execution."""
        execution = self.sql_manager.execution_list(only_one=True, id=self.execution_id)
        return execution.user_id
