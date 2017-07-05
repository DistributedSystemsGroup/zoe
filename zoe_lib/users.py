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

"""
This module contains all execution-related API calls for Zoe clients.
"""

import logging

from zoe_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeUsersAPI(ZoeAPIBase):
    """
    The users API class.
    """
    def disable(self, username):
        """
        Disables a user.

        :param username: the user to disable
        :return: True if the operation was successful, False otherwise

        :type username: str
        :rtype: bool
        """
        data = {
            'enabled': False
        }
        data, status_code = self._rest_put('/user/' + str(username), data)
        if status_code == 204:
            return
        else:
            raise ZoeAPIException(data['message'])

    def enable(self, username):
        """
        Enables a user.

        :param username: the user to enable
        :return: True if the operation was successful, False otherwise

        :type username: str
        :rtype: bool
        """
        data = {
            'enabled': True
        }
        data, status_code = self._rest_put('/user/' + str(username), data)
        if status_code == 204:
            return
        else:
            raise ZoeAPIException(data['message'])

    def list(self):
        """
        Returns a list of all users in the Zoe database.

        :return:
        """
        data, status_code = self._rest_get('/user')
        if status_code == 200:
            return data
        else:
            raise ZoeAPIException(data['message'])

    def get(self, execution_id):
        """
        Retrieve the Execution object for an existing execution.

        :param execution_id: the execution to load from the master
        :return: the Execution object, or None

        :type execution_id: int
        :rtype: dict
        """
        data, status_code = self._rest_get('/execution/' + str(execution_id))
        if status_code == 200:
            return data
        else:
            return None

    def start(self, name, application_description):
        """
        Submit an application to the master to start a new execution.

        :param name: user-provided name of the execution
        :param application_description: the application to start
        :return: the new Execution object, or None in case of error

        :type name: str
        :type application_description: dict
        :rtype: int
        """
        execution = {
            "application": application_description,
            'name': name
        }
        data, status_code = self._rest_post('/execution', execution)
        if status_code != 201:
            raise ZoeAPIException(data['message'])
        else:
            return data['execution_id']

    def endpoints(self, execution_id):
        """
        Retrieve the public endpoints exposed by a running execution.

        :param execution_id: the execution to inspect
        :return:
        """
        data, status_code = self._rest_get('/execution/endpoints/' + str(execution_id))
        if status_code == 200:
            return data['endpoints']
        else:
            return None
