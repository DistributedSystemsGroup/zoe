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

"""
This module contains all quota-related API calls for Zoe clients.
"""

import logging

from zoe_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeQuotaAPI(ZoeAPIBase):
    """
    The quota API class.
    """
    def get(self, quota_id):
        """
        Get a single quota.

        :param quota_id: the quota to retrieve
        :return:
        """
        data, status_code = self._rest_get('/quota/{}'.format(quota_id))
        if status_code != 200:
            raise ZoeAPIException(data['message'])
        else:
            return data

    def list(self):
        """
        Returns a list of all quotas in the Zoe database.

        :return:
        """
        data, status_code = self._rest_get('/quota')
        if status_code == 200:
            return data
        else:
            raise ZoeAPIException(data['message'])

    def delete(self, quota_id):
        """
        Delete a quota from the Zoe database.

        :param quota_id:
        :return:
        """
        data, status_code = self._rest_delete('/quota/{}'.format(quota_id))
        if status_code != 204:
            raise ZoeAPIException(data['message'])

    def new(self, name, cc_exec, memory, cores):
        """
        Create a new quota.

        :param name: quota name
        :param cc_exec: maximum concurrent executions
        :param memory: maximum memory
        :param cores: maximum cores
        :return:
        """
        data = {
            'name': name,
            'cc_exec': cc_exec,
            'memory': memory,
            'cores': cores
        }
        data, status_code = self._rest_post('/quota', data)
        if status_code == 201:
            return data['quota_id']
        else:
            raise ZoeAPIException(data['message'])

    def set_cc_executions(self, quota_id, cc_exec):
        """
        Sets the concurrent executions for a quota.

        :param quota_id: the quota to modify
        :param cc_exec: the amount of concurrent executions to set
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type quota_id: int
        :type cc_exec: int
        :rtype: None
        """
        data = {
            'concurrent_executions': cc_exec
        }
        data, status_code = self._rest_put('/quota/{}'.format(quota_id), data)
        if status_code != 204:
            raise ZoeAPIException(data['message'])

    def set_memory(self, quota_id, memory):
        """
        Sets the memory for a quota.

        :param quota_id: the quota to modify
        :param memory: the amount of memory to set
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type quota_id: int
        :type memory: int
        :rtype: None
        """
        data = {
            'memory': memory
        }
        data, status_code = self._rest_put('/quota/{}'.format(quota_id), data)
        if status_code != 204:
            raise ZoeAPIException(data['message'])

    def set_cores(self, quota_id, cores):
        """
        Sets the cores for a quota.

        :param quota_id: the quota to modify
        :param cores: the amount of cores to set
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type quota_id: int
        :type cores: int
        :rtype: None
        """
        data = {
            'cores': cores
        }
        data, status_code = self._rest_put('/quota/{}'.format(quota_id), data)
        if status_code != 204:
            raise ZoeAPIException(data['message'])
