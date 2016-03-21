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

from zoe_lib.users import ZoeUserAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.services import ZoeServiceAPI
from zoe_lib.info import ZoeInfoAPI
from zoe_lib.query import ZoeQueryAPI
from zoe_lib.exceptions import ZoeAPIException
from zoe_lib.predefined_apps import PREDEFINED_APPS


class ZoeClient:
    def __init__(self, url, user, password):
        """
        Create a new ZoeAPI client instance.

        :param url: the master URL
        :param user: the user name to use for the connection
        :param password: the user password
        """

        self.user_api = ZoeUserAPI(url, user, password)
        self.exec_api = ZoeExecutionsAPI(url, user, password)
        self.service_api = ZoeServiceAPI(url, user, password)
        self.query_api = ZoeQueryAPI(url, user, password)

        info_api = ZoeInfoAPI(url, user, password)
        master_info = info_api.info()
        self.deployment_name = master_info['deployment_name']

    def _validate_user_name(self, user_name):
        if '.-' in user_name:
            raise ZoeAPIException('User names cannot contain "." or "-"')

    def _validate_role(self, role_name):
        if role_name not in ['admin', 'user', 'guest']:
            raise ZoeAPIException('Roles must be one of admin, user or guest')

    def user_new(self, name, password, role):
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
        self._validate_user_name(name)
        self._validate_role(name)
        return self.user_api.create(name, password, role)

    def user_get(self, user_name):
        """
        Get a user object given a user_name.

        :param user_name: the user_name to retrieve
        :return: the user dictionary, or None

        :type user_name: str
        :rtype dict|None
        """
        self._validate_user_name(user_name)
        return self.user_api.get(user_name)

    def user_delete(self, user_name):
        """
        Delete a user given a user_name.

        :param user_name: the user_name to delete
        :return: None

        :type user_name: str
        """
        self._validate_user_name(user_name)
        return self.user_api.delete(user_name)

    def user_list(self):
        """
        Retrieves the list of users (can be used only by a user with the admin role.

        :return: a list of users
        """
        return self.query_api.query('user')

    def predefined_app_list(self):
        """
        Returns a list of predefined application available

        :return: a list of application names
        """
        name_list = []
        for gen_app in PREDEFINED_APPS:
            app = gen_app()
            name_list.append(app['name'])
        return name_list

    def predefined_app_generate(self, name):
        """
        Returns the predefined application corresponding to the name given as argument

        :param name: the name of the application to generate
        :return: an application dictionary
        """
        for gen_app in PREDEFINED_APPS:
            app = gen_app()
            if app['name'] == name:
                return app
        raise ZoeAPIException('No such predefined application')
