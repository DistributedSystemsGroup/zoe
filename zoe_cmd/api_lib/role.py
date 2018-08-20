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
This module contains all role-related API calls that a Zoe client can use.
"""
import logging

from zoe_cmd.api_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeRoleAPI(ZoeAPIBase):
    """
    The role API class.
    """
    def get(self, role_id: int) -> dict:
        """
        Retrieve a role by its ID.

        :param role_id: the service to query
        :return:

        :type role_id: int
        :rtype: dict
        """
        data, status_code = self._rest_get('/role/' + str(role_id))
        if status_code == 200:
            return data['role']
        elif status_code == 404:
            raise ZoeAPIException('role "{}" not found'.format(role_id))
        else:
            raise ZoeAPIException('error retrieving role {}: {}'.format(role_id, data))

    def delete(self, role_id: int) -> None:
        """
        Delete a role.

        :param role_id:
        :return:

        :type role_id: int
        :rtype: dict
        """
        data, status_code = self._rest_delete('/role/{}'.format(role_id))
        if status_code != 204:
            raise ZoeAPIException(data)

    def create(self, role: dict):
        """
        Create a role.

        :param role:
        :return:
        """
        data, status_code = self._rest_post('/role', role)
        if status_code != 201:
            raise ZoeAPIException(data)
        return data['role_id']

    def list(self, filters: dict):
        """
        List roles, with an optional filter.

        :param filters: a dictionary with zero or more keys: rolename, email, priority, enables, auth_source, role_id, quota_id
        :return:
        """
        data, status_code = self._rest_get('/role', filters)
        if status_code != 200:
            raise ZoeAPIException(data)
        return list(data.values())

    def update(self, role_id: int, entries: dict) -> None:
        """
        Update a role.

        :param role_id:
        :param entries:
        :return:
        """
        data, status_code = self._rest_post('/role/{}'.format(role_id), entries)
        if status_code != 201:
            raise ZoeAPIException(data)
