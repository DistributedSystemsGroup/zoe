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
This module contains all user-related API calls that a Zoe client can use.

For now Zoe implements a bare minimum of user management.
"""
from zoe_lib import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException


class ZoeUserAPI(ZoeAPIBase):
    """
    The UserAPI class has methods for interacting with Zoe's user system.
    """

    def exists(self, user_id: int) -> bool:
        """
        Checks if a given user_id exists.

        :param user_id: the user_id to check
        :return: True if the user_id exists, False otherwise
        """
        user, status_code = self._rest_get('/user/' + str(user_id))
        return status_code == 200

    def create(self, name: str, password: str, role: str):
        """
        Creates a new user, given his email address.

        :param name: the user name address
        :param password: the user password
        :param role: the user role
        :return: the new user ID
        """
        data = {
            'name': name,
            'password': password,
            'role': role
        }
        user_id, status_code = self._rest_post('/user', data)
        if status_code == 201:
            return user_id['user_id']
        else:
            raise ZoeAPIException(user_id['message'])

    def get(self, user_id: int):
        """
        Get a user object given a user_id.

        :param user_id: the user_id to look for
        :return: the user dictionary, or None
        """
        user, status_code = self._rest_get('/user/' + str(user_id))
        if status_code == 200:
            return user
        else:
            return None

    def delete(self, user_id: int):
        """
        Delete a user given a user_id.

        :param user_id: the user_id to delete
        :return: None
        """
        data, status_code = self._rest_delete('/user/' + str(user_id))
        if status_code != 204:
            raise ZoeAPIException(data['message'])
