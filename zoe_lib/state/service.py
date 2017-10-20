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

log = logging.getLogger(__name__)


class ResourceLimits:
    """A resource limits description."""
    def __init__(self, data, unit):
        if isinstance(data, dict):
            self.min = data['min']
            self.max = data['max']
        elif isinstance(data, ResourceLimits):
            self.min = data.min
            self.max = data.max
        elif isinstance(data, int):
            self.min = data
            self.max = data
        else:
            raise TypeError
        self.unit = unit

        if self.min is None:
            self.min = 0
        if self.max is None:
            self.max = 0

    def __add__(self, other):
        if isinstance(other, ResourceLimits) and self.unit == other.unit:
            res = {
                'min': self.min + other.min,
                'max': self.max + other.max
            }
            return ResourceLimits(res, self.unit)
        else:
            raise NotImplementedError


class ResourceReservation:
    """The resources reserved by a Service."""
    def __init__(self, data):
        self.memory = ResourceLimits(data['memory'], "bytes")
        self.cores = ResourceLimits(data['cores'], 'units')

    def __add__(self, other):
        if isinstance(other, ResourceReservation):
            res = {
                'memory': self.memory + other.memory,
                'cores': self.cores + other.cores
            }
            return ResourceReservation(res)
        else:
            return NotImplemented


class VolumeDescription:
    """A generic description for container volumes."""
    def __init__(self, vtype: str):
        self.type = vtype


class VolumeDescriptionHostPath(VolumeDescription):
    """Host-based volumes."""
    def __init__(self, name: str, path: str, readonly: bool):
        super().__init__("host_directory")
        self.path = path
        self.mount_point = '/mnt/' + name
        self.readonly = readonly


class Service:
    """A Zoe Service."""

    CREATED_STATUS = 'created'
    TERMINATING_STATUS = "terminating"
    INACTIVE_STATUS = "inactive"
    ACTIVE_STATUS = "active"
    STARTING_STATUS = "starting"
    ERROR_STATUS = "error"
    RUNNABLE_STATUS = "runnable"

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
        self.backend_host = d['backend_host']

        self.ip_address = d['ip_address']
        if self.ip_address is not None and ('/32' in self.ip_address or '/128' in self.ip_address):
            self.ip_address = self.ip_address.split('/')[0]

        self.essential = d['essential']

        # Fields parsed from the JSON description
        try:
            self.image_name = self.description['image']
        except KeyError:
            self.image_name = self.description['docker_image']  # zapp description v2

        self.is_monitor = self.description['monitor']
        self.startup_order = self.description['startup_order']

        try:
            self.environment = self.description['environment']
        except KeyError:
            self.environment = []

        try:
            self.command = self.description['command']
        except KeyError:
            self.command = None

        try:
            self.work_dir = self.description['work_dir']
        except KeyError:
            self.work_dir = None

        try:
            self.resource_reservation = ResourceReservation(self.description['resources'])
        except KeyError:
            self.resource_reservation = ResourceReservation({'memory': self.description['required_resources']['memory'], 'cores': 0})  # ZApp description v2

        try:
            self.volumes = [VolumeDescriptionHostPath(v['name'], v['path'], v['read_only']) for v in self.description['volumes']]
        except KeyError:
            self.volumes = []
        except TypeError:
            self.volumes = [VolumeDescriptionHostPath(v[0], v[1], v[2]) for v in self.description['volumes']]

        try:
            self.labels = self.description['labels']
        except KeyError:
            self.labels = []

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
            'backend_status': self.backend_status,
            'backend_host': self.backend_host,
            'essential': self.essential,
            'proxy_address': self.proxy_address
        }

    def __eq__(self, other):
        return self.id == other.id

    def set_terminating(self):
        """The service is being terminated."""
        self.sql_manager.service_update(self.id, status=self.TERMINATING_STATUS)
        self.status = self.TERMINATING_STATUS

    def set_inactive(self):
        """The service must not run."""
        self.sql_manager.service_update(self.id, status=self.INACTIVE_STATUS)
        self.status = self.INACTIVE_STATUS

    def set_starting(self):
        """The service is being started by the back-end."""
        self.sql_manager.service_update(self.id, status=self.STARTING_STATUS)
        self.status = self.STARTING_STATUS

    def set_runnable(self):
        """The service is elastic and can be started."""
        self.sql_manager.service_update(self.id, status=self.RUNNABLE_STATUS)
        self.status = self.RUNNABLE_STATUS

    def set_active(self, backend_id, ip_address, ports):
        """The service is running and has a valid backend_id."""
        self.sql_manager.service_update(self.id, status=self.ACTIVE_STATUS, backend_id=backend_id, error_message=None, ip_address=ip_address, backend_status=self.BACKEND_START_STATUS)
        self.error_message = None
        self.ip_address = ip_address
        self.backend_id = backend_id
        self.status = self.ACTIVE_STATUS
        self.backend_status = self.BACKEND_START_STATUS
        for port in self.ports:
            if port.internal_name in ports and ports[port.internal_name] is not None:
                port.activate(ip_address, ports[port.internal_name])
            else:
                port.reset()

    def set_error(self, error_message):
        """The service could not be created/started."""
        self.sql_manager.service_update(self.id, status=self.ERROR_STATUS, error_message=error_message)
        self.status = self.ERROR_STATUS
        self.error_message = error_message

    def set_backend_status(self, new_status):
        """The backend status of the service has changed."""
        log.debug("service {}, backend status updated to {}".format(self.id, new_status))
        self.backend_status = new_status
        if self.is_dead():
            for port in self.ports:
                port.reset()
            self.ip_address = None
            self.sql_manager.service_update(self.id, backend_status=new_status, ip_address=None)
            if new_status == self.BACKEND_DESTROY_STATUS:
                self.backend_id = None
                self.sql_manager.service_update(self.id, backend_status=new_status, backend_id=None, ip_address=None)
            else:
                self.sql_manager.service_update(self.id, backend_status=new_status, ip_address=None)
        else:
            self.sql_manager.service_update(self.id, backend_status=new_status)

    def assign_backend_host(self, backend_host):
        """Assign this service to a host in particular."""
        self.sql_manager.service_update(self.id, backend_host=backend_host)
        log.debug('service {} assigned to host {}'.format(self.id, backend_host))
        self.backend_host = backend_host

    @property
    def dns_name(self):
        """Getter for the DNS name of this service as it will be registered in Docker's DNS."""
        return "{}-{}-{}".format(self.name, self.execution_id, get_conf().deployment_name)

    @property
    def user_id(self):
        """Getter for the user_id, that is actually taken from the parent execution."""
        execution = self.sql_manager.execution_list(only_one=True, id=self.execution_id)
        return execution.user_id

    @property
    def ports(self):
        """Getter for the ports exposed by this service."""
        return self.sql_manager.port_list(service_id=self.id)

    @property
    def proxy_address(self):
        """Get proxy address path"""
        if len(self.ports) > 0:
            return self.name + "-" + str(self.execution_id) + "-" + get_conf().deployment_name + "." + get_conf().proxy_path
        else:
            return None

    def is_dead(self):
        """Returns True if this service is not running."""
        return self.backend_status != self.BACKEND_START_STATUS

    @property
    def unique_name(self):
        """Returns a name for this service that is unique across multiple Zoe instances running on the same backend."""
        return self.name + '-' + str(self.execution_id) + '-' + get_conf().deployment_name

    @property
    def execution(self):
        """Return the parent execution."""
        return self.sql_manager.execution_list(only_one=True, id=self.execution_id)
