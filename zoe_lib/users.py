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
from zoe_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException


class ZoeUserAPI(ZoeAPIBase):
    """
    The UserAPI class has methods for interacting with Zoe's user system.
    """
    def create(self, name, password, role):
        """
        Creates a new user.

        :param name: the user name address
        :param password: the user password
        :param role: the user role
        :return: the new user ID

        :type name: str
        :type password: str
        :type role: str
        """
        data = {
            'name': name,
            'password': password,
            'role': role
        }
        user, status_code = self._rest_post('/user', data)
        if status_code == 201:
            return user
        else:
            raise ZoeAPIException(user['message'])

    def get(self, user_name):
        """
        Get a user object given a user_name.

        :param user_name: the user_name to retrieve
        :return: the user dictionary, or None

        :type user_name: str
        :rtype: dict|None
        """
        user, status_code = self._rest_get('/user/' + user_name)
        if status_code == 200:
            return user
        else:
            return None

    def delete(self, user_name):
        """
        Delete a user given a user_name.

        :param user_name: the user_name to delete
        :return: None

        :type user_name: str
        """
        data, status_code = self._rest_delete('/user/' + str(user_name))
        if status_code != 204:
            raise ZoeAPIException(data['message'])
