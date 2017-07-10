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
This module contains all user-related API calls for Zoe clients.
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
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type username: str
        :rtype: None
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
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type username: str
        :rtype: None
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

    def set_email(self, username, email):
        """
        Sets the email address for a user.

        :param username: the user to enable
        :param email: the email to set
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type username: str
        :rtype: bool
        """
        data = {
            'email': email
        }
        data, status_code = self._rest_put('/user/' + str(username), data)
        if status_code == 200:
            return
        else:
            raise ZoeAPIException(data['message'])

    def set_role(self, username, role):
        """
        Sets the role for a user.

        :param username: the user to enable
        :param role: the role to set
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type username: str
        :rtype: bool
        """
        data = {
            'role': role
        }
        data, status_code = self._rest_put('/user/' + str(username), data)
        if status_code == 200:
            return
        else:
            raise ZoeAPIException(data['message'])

    def set_quota(self, username, quota_id):
        """
        Sets the email address for a user.

        :param username: the user to modify
        :param quota_id: the quota ID to associate to this user
        :return: None if the operation was successful, raises ZoeAPIException otherwise

        :type username: str
        :rtype: bool
        """
        data = {
            'quota_id': quota_id
        }
        data, status_code = self._rest_put('/user/' + str(username), data)
        if status_code == 200:
            return
        else:
            raise ZoeAPIException(data['message'])
