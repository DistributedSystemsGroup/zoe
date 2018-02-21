# Copyright (c) 2018, Daniele Venzano
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
This module contains all quota-related API calls that a Zoe client can use.
"""
import logging

from zoe_cmd.api_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeQuotaAPI(ZoeAPIBase):
    """
    The quota API class.
    """
    def get(self, quota_id: int) -> dict:
        """
        Retrieve a quota by its ID.

        :param quota_id: the service to query
        :return:

        :type quota_id: int
        :rtype: dict
        """
        data, status_code = self._rest_get('/quota/' + str(quota_id))
        if status_code == 200:
            return data['quota']
        elif status_code == 404:
            raise ZoeAPIException('quota "{}" not found'.format(quota_id))
        else:
            raise ZoeAPIException('error retrieving quota {}: {}'.format(quota_id, data))

    def delete(self, quota_id: int) -> None:
        """
        Delete a quota.

        :param quota_id:
        :return:

        :type quota_id: int
        :rtype: dict
        """
        data, status_code = self._rest_delete('/quota/{}'.format(quota_id))
        if status_code != 204:
            raise ZoeAPIException(data)

    def create(self, quota: dict):
        """
        Create a quota.

        :param quota:
        :return:
        """
        data, status_code = self._rest_post('/quota', quota)
        if status_code != 201:
            raise ZoeAPIException(data)
        return data['quota_id']

    def list(self, filters: dict):
        """
        List quotas, with an optional filter.

        :param filters: a dictionary with zero or more keys: quotaname, email, priority, enables, auth_source, quota_id, quota_id
        :return:
        """
        data, status_code = self._rest_get('/quota', filters)
        if status_code != 200:
            raise ZoeAPIException(data)
        return data

    def update(self, quota_id: int, entries: dict) -> None:
        """
        Update a quota.

        :param quota_id:
        :param entries:
        :return:
        """
        data, status_code = self._rest_post('/quota/{}'.format(quota_id), entries)
        if status_code != 201:
            raise ZoeAPIException(data)
