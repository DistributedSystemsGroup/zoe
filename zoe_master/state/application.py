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

from zoe_lib.exceptions import InvalidApplicationDescription


class ApplicationDescription:
    def __init__(self):

        self.name = ''
        self.version = 0
        self.will_end = True
        self.priority = 512
        self.requires_binary = False
        self.services = []

    def to_dict(self):
        d = {
            'name': self.name,
            'version': self.version,
            'will_end': self.will_end,
            'priority': self.priority,
            'requires_binary': self.requires_binary,
            'services': []
        }
        for p in self.services:
            d['services'].append(p.to_dict())

        return d

    def from_dict(self, data):
        try:
            self.name = data['name']
        except KeyError:
            raise InvalidApplicationDescription(msg="Missing required key: name")

        try:
            self.version = int(data['version'])
        except ValueError:
            raise InvalidApplicationDescription(msg="version field should be an int")
        except KeyError:
            raise InvalidApplicationDescription(msg="Missing required key: version")

        try:
            self.will_end = bool(data['will_end'])
        except ValueError:
            raise InvalidApplicationDescription(msg="will_end field must be a boolean")

        try:
            self.requires_binary = bool(data['requires_binary'])
        except ValueError:
            raise InvalidApplicationDescription(msg="requires_binary field must be a boolean")

        try:
            self.priority = int(data['priority'])
        except ValueError:
            raise InvalidApplicationDescription("priority field must be an int")
        if self.priority < 0 or self.priority > 1024:
            raise InvalidApplicationDescription("priority must be between 0 and 1024")

        for p in data['services']:
            aux = ServiceDescription()
            aux.from_dict(p)
            self.services.append(aux)

        found_monitor = False
        for p in self.services:
            if p.monitor:
                found_monitor = True
                break
        if not found_monitor:
            raise InvalidApplicationDescription("at least one service should have monitor set to True")

    def total_memory(self) -> int:
        memory = 0
        for p in self.services:
            memory += p.required_resources['memory']
        return memory

    def service_count(self) -> int:
        return len(self.services)


class ServiceEndpointDescription:
    def __init__(self):
        self.name = ''
        self.protocol = ''
        self.port_number = 0
        self.path = ''
        self.is_main_endpoint = False

    def to_dict(self):
        d = {
            'name': self.name,
            'protocol': self.protocol,
            'port_number': self.port_number,
            'path': self.path,
            'is_main_endpoint': self.is_main_endpoint
        }
        return d

    def from_dict(self, data):
        required_keys = ['name', 'protocol', 'port_number', 'is_main_endpoint']
        for k in required_keys:
            try:
                setattr(self, k, data[k])
            except KeyError:
                raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

        try:
            self.port_number = int(self.port_number)
        except ValueError:
            raise InvalidApplicationDescription(msg="port_number field should be an integer")

        try:
            self.is_main_endpoint = bool(self.is_main_endpoint)
        except ValueError:
            raise InvalidApplicationDescription(msg="is_main_endpoint field should be a boolean")

        if 'path' in data:
            self.path = data['path']

    def get_url(self, address):
        return self.protocol + "://" + address + ":{}".format(self.port_number) + self.path


class ServiceDescription:
    def __init__(self):
        self.name = ''
        self.version = 0
        self.docker_image = ''
        self.monitor = False  # if this service dies, the whole application is considered as complete and the execution is terminated
        self.ports = []  # A list of ServiceEndpoints
        self.required_resources = {}
        self.environment = []  # Environment variables to pass to Docker
        self.volumes = []  # list of volumes to mount. Each volume is a three tuple: host path, container path, readonly boolean
        self.networks = []  # additional networks IDs this container should be connected to
        self.command = None  # Commandline to pass to the Docker container

    def to_dict(self):
        d = {
            'name': self.name,
            'docker_image': self.docker_image,
            'monitor': self.monitor,
            'required_resources': self.required_resources,
            'environment': self.environment,
            'command': self.command,
            'ports': [],
            'volumes': [],
            'networks': []
        }
        for p in self.ports:
            d['ports'].append(p.to_dict())
        return d

    def from_dict(self, data):
        required_keys = ['name', 'docker_image', 'monitor']
        for k in required_keys:
            try:
                setattr(self, k, data[k])
            except KeyError:
                raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

        try:
            self.monitor = bool(self.monitor)
        except ValueError:
            raise InvalidApplicationDescription(msg="monitor field should be a boolean")

        if 'ports' not in data:
            raise InvalidApplicationDescription(msg="Missing required key: ports")
        if not hasattr(data['ports'], '__iter__'):
            raise InvalidApplicationDescription(msg='ports should be an iterable')
        for pp in data['ports']:
            aux = ServiceEndpointDescription()
            aux.from_dict(pp)
            self.ports.append(aux)

        if 'required_resources' not in data:
            raise InvalidApplicationDescription(msg="Missing required key: required_resources")
        if not isinstance(data['required_resources'], dict):
            raise InvalidApplicationDescription(msg="required_resources should be a dictionary")
        if 'memory' not in data['required_resources']:
            raise InvalidApplicationDescription(msg="Missing required key: required_resources -> memory")

        self.required_resources = data['required_resources'].copy()
        try:
            self.required_resources['memory'] = int(self.required_resources['memory'])
        except ValueError:
            raise InvalidApplicationDescription(msg="required_resources -> memory field should be an int")

        if 'environment' in data:
            if not hasattr(data['environment'], '__iter__'):
                raise InvalidApplicationDescription(msg='environment should be an iterable')
            self.environment = data['environment'].copy()
            for e in self.environment:
                if len(e) != 2:
                    raise InvalidApplicationDescription(msg='environment variable should have a name and a value')
                if not isinstance(e[0], str):
                    raise InvalidApplicationDescription(msg='environment variable names must be strings: {}'.format(e[0]))
                if not isinstance(e[1], str):
                    raise InvalidApplicationDescription(msg='environment variable values must be strings: {}'.format(e[1]))

        if 'command' in data:
            self.command = data['command']

        if 'volumes' in data:
            if not hasattr(data['volumes'], '__iter__'):
                raise InvalidApplicationDescription(msg='volumes should be an iterable')
            self.volumes = data['volumes'].copy()
            for v in self.volumes:
                if len(v) != 3:
                    raise InvalidApplicationDescription(msg='volume description should have three components')
                if not isinstance(v[2], bool):
                    raise InvalidApplicationDescription(msg='readonly volume item (third) must be a boolean: {}'.format(v[2]))

        if 'networks' in data:
            if not hasattr(data['networks'], '__iter__'):
                raise InvalidApplicationDescription(msg='networks should be an iterable')
            self.networks = data['networks'].copy()
