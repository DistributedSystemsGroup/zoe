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

import re

import tornado.web

from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.utils import get_auth_login, catch_exceptions
from zoe_api.web.custom_request_handler import ZoeRequestHandler
from zoe_api.exceptions import ZoeAuthException


class RootWeb(ZoeRequestHandler):
    """Handler class"""

    @tornado.web.authenticated
    def get(self):
        """Home page."""
        self.redirect('/home')


class LoginWeb(ZoeRequestHandler):
    """The login web page."""
    def get(self):
        """Login page."""
        why = self.get_argument('why', None)
        self.render('login.html', **{'why': why})

    def post(self):
        """Try to authenticate."""
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        if not re.match(r'[a-zA-Z0-9]+', username) or len(password) == 0:
            self.redirect('/login?why=invalid')

        try:
            uid, role = get_auth_login(self.application.api_endpoint, username, password)
        except ZoeAuthException as e:
            self.redirect('/login?why={}'.format(e.message))
            return

        self.set_secure_cookie('zoe_web_user', uid)
        self.redirect('/home')


class LogoutWeb(ZoeRequestHandler):
    """The logout web page."""

    def get(self):
        """Logout and redirect to login page."""
        self.clear_cookie('zoe_web_user')
        self.redirect('/login')


class HomeWeb(ZoeRequestHandler):
    """Handler class"""

    @tornado.web.authenticated
    def get(self):
        """Home page with authentication."""
        filters = {
            'user_id': self.current_user.username,
            'status': 'running'
        }
        executions = self.api_endpoint.execution_list(self.current_user, **filters)
        filters['status'] = 'starting'
        executions += self.api_endpoint.execution_list(self.current_user, **filters)
        filters['status'] = 'scheduled'
        executions += self.api_endpoint.execution_list(self.current_user, **filters)
        filters['status'] = 'terminated'
        filters['limit'] = 5
        executions += self.api_endpoint.execution_list(self.current_user, **filters)

        template_vars = {
            'executions': sorted(executions, key=lambda e: e.id),
            'user': self.current_user
        }
        self.render('home_user.html', **template_vars)
