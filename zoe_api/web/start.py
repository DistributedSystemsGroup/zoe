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
        self.redirect("/user")


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


class LogoutWeb(ZoeRequestHandler):
    """The logout web page."""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self):
        """Login page."""
        self.clear_cookie('zoe')
        self.redirect(self.get_argument("next", u"/login"))


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
        if uid is None:
            self.redirect(self.get_argument('next', u'/login'))
            return

        filters = {
            "user_id": uid,
            "limit": 5
        }
        last_executions = self.api_endpoint.execution_list(uid, role, **filters)

        filters = {
            "user_id": uid,
            "status": "running"
        }
        last_running_executions = self.api_endpoint.execution_list(uid, role, **filters)

        filters = {
            "user_id": uid,
            "status": "submitted"
        }
        last_running_executions += self.api_endpoint.execution_list(uid, role, **filters)

        filters = {
            "user_id": uid,
            "status": "scheduled"
        }
        last_running_executions += self.api_endpoint.execution_list(uid, role, **filters)

        filters = {
            "user_id": uid,
            "status": "starting"
        }
        last_running_executions += self.api_endpoint.execution_list(uid, role, **filters)

        running_reservations = [e.total_reservations for e in last_running_executions]
        total_memory = sum([r.memory.min for r in running_reservations])
        total_cores = sum([r.cores.min for r in running_reservations])

        template_vars = {
            "uid": uid,
            "role": role,
            "total_memory": total_memory,
            "total_cores": total_cores,
            'last_executions': sorted(last_executions, key=lambda e: e.id),
            'running_executions': sorted(last_running_executions, key=lambda e: e.id)
        }
        self.render('home_user.html', **template_vars)
