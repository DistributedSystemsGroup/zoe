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

from zoe_api.web.request_handler import ZoeWebRequestHandler
from zoe_api.auth.base import BaseAuthenticator


class RootWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """Home page without authentication."""
        self.redirect("/user")


class LoginWeb(ZoeWebRequestHandler):
    """The login web page."""

    def get(self):
        """Login page."""
        self.render('login.html')

    def post(self):
        """Try to authenticate."""
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        user = BaseAuthenticator().full_auth(username, password)

        if not self.get_secure_cookie('zoe'):
            cookie_val = user.username
            self.set_secure_cookie('zoe', cookie_val)
        self.redirect(self.get_argument("next", u"/user"))


class LogoutWeb(ZoeWebRequestHandler):
    """The logout web page."""

    def get(self):
        """Login page."""
        self.clear_cookie('zoe')
        self.redirect(self.get_argument("next", u"/login"))


class HomeWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """Home page with authentication."""
        if self.current_user is None:
            return

        filters = {
            "user_id": self.current_user,
            "limit": 5
        }
        last_executions = self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user,
            "status": "running"
        }
        last_running_executions = self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user,
            "status": "submitted"
        }
        last_running_executions += self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user,
            "status": "scheduled"
        }
        last_running_executions += self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user,
            "status": "starting"
        }
        last_running_executions += self.api_endpoint.execution_list(self.current_user, **filters)

        running_reservations = [e.total_reservations for e in last_running_executions]
        total_memory = sum([r.memory.max for r in running_reservations])
        total_cores = sum([r.cores.max for r in running_reservations])

        template_vars = {
            "user": self.current_user,
            "total_memory": total_memory,
            "total_cores": total_cores,
            'last_executions': sorted(last_executions, key=lambda e: e.id),
            'running_executions': sorted(last_running_executions, key=lambda e: e.id)
        }
        self.render('home_user.html', **template_vars)
