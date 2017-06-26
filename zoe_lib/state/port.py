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

from zoe_lib.state.base import Base

log = logging.getLogger(__name__)


class ExposedPort:
    """A port on the container that should be exposed."""
    def __init__(self, data):
        self.proto = data['protocol']
        self.number = data['port_number']
        self.external_ip = None
        self.external_port = None

    def __eq__(self, other):
        if isinstance(other, ExposedPort):
            return other.proto == self.proto and other.number == self.number
        elif isinstance(other, str):
            return other == str(self.number) + "/" + self.proto
        else:
            return NotImplemented


class Port(Base):
    """A tcp or udp port that should be exposed by the backend."""

    def __init__(self, d, sql_manager):
        super().__init__(d, sql_manager)

        self.internal_name = d['internal_name']
        self.external_ip = d['external_ip']
        self.external_port = d['external_port']
        self.description = d['description']

        self.internal_number = self.description['port_number']
        self.protocol = self.description['protocol']
        self.url_template = self.description['url_template']

    def serialize(self):
        """Generates a dictionary that can be serialized in JSON."""
        return {
            'id': self.id,
            'internal_name': self.internal_name,
            'external_ip': self.external_ip,
            'external_port': self.external_port,
            'description': self.description
        }

    def activate(self, ext_ip, ext_port):
        """The backend has exposed the port."""
        self.sql_manager.port_update(self.id, external_ip=ext_ip, external_port=ext_port)
        self.external_port = ext_port
        self.external_ip = ext_ip

    def reset(self):
        """The backend has stopped exposing the port."""
        self.sql_manager.port_update(self.id, external_ip=None, external_port=None)
        self.external_port = None
        self.external_ip = None
