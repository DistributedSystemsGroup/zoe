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

from zoe_lib import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeExecutionsAPI(ZoeAPIBase):
    """
    The execution API class.
    """
    def terminate(self, execution_id: int) -> bool:
        """
        Terminates an execution.

        :param execution_id: the execution to delete
        :return: True is the operation was successful, False otherwise
        """
        data, status_code = self._rest_delete('/execution/' + str(execution_id))
        if status_code == 204:
            return
        else:
            raise ZoeAPIException(data['message'])

    def list(self):
        """
        Returns a list of all executions for the calling user, all of them if the user is admin.

        :return:
        """
        data, status_code = self._rest_get('/execution')
        if status_code == 200:
            return data
        else:
            raise ZoeAPIException(data['message'])

    def execution_get(self, execution_id: int) -> dict:
        """
        Retrieve the Execution object for an existing execution.

        :param execution_id: the execution to load from the master
        :return: the Execution object, or None
        """
        data, status_code = self._rest_get('/execution/' + str(execution_id))
        if status_code == 200:
            return data
        else:
            return None

    def execution_start(self, name: str, application_description: dict) -> int:
        """
        Submit an application to the master to start a new execution.

        :param name: user-provided name of the execution
        :param application_description: the application to start
        :return: the new Execution object, or None in case of error
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
