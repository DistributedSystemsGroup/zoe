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
This module contains all user-related API calls that a Zoe client can use.
"""
import logging

from zoe_cmd.api_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeUserAPI(ZoeAPIBase):
    """
    The user API class.
    """
    def get(self, user_id: int) -> dict:
        """
        Retrieve a user by its ID.

        :param user_id: the service to query
        :return:

        :type user_id: int
        :rtype: dict
        """
        data, status_code = self._rest_get('/user/' + str(user_id))
        if status_code == 200:
            return data['user']
        elif status_code == 404:
            raise ZoeAPIException('user "{}" not found'.format(user_id))
        else:
            raise ZoeAPIException('error retrieving user {}: {}'.format(user_id, data))

    def delete(self, user_id: int) -> None:
        """
        Delete a user.

        :param user_id:
        :return:

        :type user_id: int
        :rtype: dict
        """
        data, status_code = self._rest_delete('/user/{}'.format(user_id))
        if status_code != 204:
            raise ZoeAPIException(data)

    def create(self, user: dict):
        """
        Create a user.

        :param user:
        :return:
        """
        data, status_code = self._rest_post('/user', user)
        if status_code != 201:
            raise ZoeAPIException(data)
        return data['user_id']

    def list(self, filters):
        """
        List users, with an optional filter.

        :param filters: a dictionary with zero or more keys: username, email, priority, enables, auth_source, role_id, quota_id
        :return:
        """
        data, status_code = self._rest_get('/user', filters)
        if status_code != 200:
            raise ZoeAPIException(data)
        return data

    def update(self, user_id: int, entries) -> None:
        """
        Update a user.

        :param user_id:
        :param entries:
        :return:
        """
        data, status_code = self._rest_post('/user/{}'.format(user_id), entries)
        if status_code != 201:
            raise ZoeAPIException(data)
