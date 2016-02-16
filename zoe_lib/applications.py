# Copyright (c) 2015, Daniele Venzano
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

"""
This module all application-related API calls for Zoe clients.
"""

import logging

from zoe_lib import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException, InvalidApplicationDescription

log = logging.getLogger(__name__)


class ZoeApplicationAPI(ZoeAPIBase):
    """
    The application API.
    """
    def get(self, application_id: int) -> dict:
        """
        Return an Application object

        :param application_id: the identifier of the application
        :return: the application dict
        """
        data, status_code = self._rest_get('/application/' + str(application_id))
        if status_code == 200:
            return data
        else:
            raise ZoeAPIException(data['message'])

    def create(self, description: dict) -> int:
        """
        Create a new application and commit it to the database.

        :param description: the application description
        :return: the new application ID
        """
        self._app_check(description)

        data, status_code = self._rest_post('/application', description)
        if status_code != 201:
            raise ZoeAPIException(data['message'])

        return data['application_id']

    def delete(self, application_id: int):
        """
        If the application does not exists an error will be logged.

        :param application_id: the application to delete
        """
        data, status_code = self._rest_delete('/application/' + str(application_id))
        if status_code != 204:
            raise ZoeAPIException(data['message'])

    def _app_check(self, data):
        required_keys = ['name', 'will_end', 'priority', 'requires_binary', 'version']
        for k in required_keys:
            if k not in data:
                raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

        try:
            int(data["version"])
        except ValueError:
            raise InvalidApplicationDescription(msg="version field should be an int")

        try:
            bool(data['will_end'])
        except ValueError:
            raise InvalidApplicationDescription(msg="will_end field must be a boolean")

        try:
            bool(data['requires_binary'])
        except ValueError:
            raise InvalidApplicationDescription(msg="requires_binary field must be a boolean")

        try:
            priority = int(data['priority'])
        except ValueError:
            raise InvalidApplicationDescription(msg="priority field must be an int")
        if priority < 0 or priority > 1024:
            raise InvalidApplicationDescription(msg="priority must be between 0 and 1024")

        for p in data['processes']:
            self._process_check(p)

        found_monitor = False
        for p in data['processes']:
            if p['monitor']:
                found_monitor = True
                break
        if not found_monitor:
            raise InvalidApplicationDescription(msg="at least one process should have monitor set to True")

    def _process_check(self, data):
        required_keys = ['name', 'docker_image', 'monitor', 'ports', 'required_resources']
        for k in required_keys:
            if k not in data:
                raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

        try:
            bool(data['monitor'])
        except ValueError:
            raise InvalidApplicationDescription(msg="monitor field should be a boolean")

        if not hasattr(data['ports'], '__iter__'):
            raise InvalidApplicationDescription(msg='ports should be a list')
        for pp in data['ports']:
            self._port_check(pp)

        if not isinstance(data['required_resources'], dict):
            raise InvalidApplicationDescription(msg="required_resources should be a dictionary")
        if 'memory' not in data['required_resources']:
            raise InvalidApplicationDescription(msg="Missing required key: required_resources -> memory")
        try:
            int(data['required_resources']['memory'])
        except ValueError:
            raise InvalidApplicationDescription(msg="required_resources -> memory field should be an int")

        if 'environment' in data:
            if not hasattr(data['environment'], '__iter__'):
                raise InvalidApplicationDescription(msg='environment should be an iterable')
            for e in data['environment']:
                if len(e) != 2:
                    raise InvalidApplicationDescription(msg='environment variable should have a name and a value')
                if not isinstance(e[0], str):
                    raise InvalidApplicationDescription(msg='environment variable names must be strings: {}'.format(e[0]))
                if not isinstance(e[1], str):
                    raise InvalidApplicationDescription(msg='environment variable values must be strings: {}'.format(e[1]))

    def _port_check(self, data):
        required_keys = ['name', 'protocol', 'port_number', 'is_main_endpoint']
        for k in required_keys:
            if k not in data:
                raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

        try:
            int(data['port_number'])
        except ValueError:
            raise InvalidApplicationDescription(msg="port_number field should be an integer")

        try:
            bool(data['is_main_endpoint'])
        except ValueError:
            raise InvalidApplicationDescription(msg="is_main_endpoint field should be a boolean")
