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

"""Main points of entry for the Zoe web interface."""

from random import randint
import json

from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.utils import get_auth_login, get_auth, catch_exceptions
from zoe_api.web.custom_request_handler import ZoeRequestHandler


class RootWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self):
        """Home page without authentication."""
        self.render('index.html')


class LoginWeb(ZoeRequestHandler):
    """The login web page."""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self):
        """Login page."""
        self.render('login.html')

    @catch_exceptions
    def post(self):
        """Try to authenticate."""
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        uid, role = get_auth_login(username, password)

        if not self.get_secure_cookie('zoe'):
            cookie_val = uid + '.' + role
            self.set_secure_cookie('zoe', cookie_val)
        self.redirect(self.get_argument("next", u"/user"))


class HomeWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self):
        """Home page with authentication."""
        uid, role = get_auth(self)

        if role == 'user' or role == 'admin':
            executions = self.api_endpoint.execution_list(uid, role)

            template_vars = {
                'executions': sorted(executions, key=lambda e: e.id),
                'is_admin': role == 'admin',
            }
            self.render('home_user.html', **template_vars)
        else:
            template_vars = {
                'refresh': randint(2, 8),
                'execution_status': 'Please wait...',
                'execution_urls': [],
            }

            app_descr = json.load(open('contrib/zoeapps/eurecom_aml_lab.json', 'r'))
            execution = self.api_endpoint.execution_list(uid, role, name='aml-lab')
            if len(execution) == 0 or execution[0]['status'] == 'terminated' or execution[0]['status'] == 'finished':
                self.api_endpoint.execution_start(uid, role, 'aml-lab', app_descr)
                template_vars['execution_status'] = 'submitted'
                return self.render('home_guest.html', **template_vars)
            else:
                execution = execution[0]
                if execution['status'] != 'running':
                    template_vars['execution_status'] = execution['status']
                    return self.render('home_guest.html', **template_vars)
                else:
                    template_vars['refresh'] = -1
                    template_vars['execution_status'] = execution['status']
                    return self.render('home_guest.html', **template_vars)
