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

import os
import subprocess

from zoe_api.web.request_handler import ZoeWebRequestHandler
from zoe_api.auth.base import BaseAuthenticator
from zoe_api.auth.requests_oauth2 import EurecomGitLabClient

import zoe_lib.config


class RootWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """Home page without authentication."""
        self.redirect(self.reverse_url("login"))


class LoginWeb(ZoeWebRequestHandler):
    """The login web page."""

    def get(self):
        """Login page."""
        template_vars = {}
        if zoe_lib.config.get_conf().oauth_client_id != '':
            template_vars['with_gitlab_oauth'] = True
        self.render('login.jinja2', **template_vars)

    def post(self):
        """Try to authenticate."""
        login_type = self.get_argument('login', 'userpass')
        if login_type == 'OAUTH':
            egitlab = EurecomGitLabClient(client_id=zoe_lib.config.get_conf().oauth_client_id, client_secret=zoe_lib.config.get_conf().oauth_client_secret, redirect_uri=zoe_lib.config.get_conf().oauth_redirect_uri)
            auth_url = egitlab.authorize_url(scope=['openid', 'read_user'], response_type='code')
            self.redirect(auth_url)
            return
        else:
            username = self.get_argument("username", "")
            password = self.get_argument("password", "")
            user = BaseAuthenticator().full_auth(username, password)
            if user is None:
                self.redirect(self.reverse_url("login"))
                return

            if not self.get_secure_cookie('zoe'):
                cookie_val = user.username
                self.set_secure_cookie('zoe', cookie_val)
            self.redirect(self.get_argument("next", self.reverse_url("home_user")))


class LogoutWeb(ZoeWebRequestHandler):
    """The logout web page."""

    def get(self):
        """Login page."""
        self.clear_cookie('zoe')
        self.redirect(self.reverse_url("login"))


class HomeWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """Home page with authentication."""
        if self.current_user is None:
            return

        filters = {
            "user_id": self.current_user.id,
            "limit": 5
        }
        last_executions = self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user.id,
            "status": "running"
        }
        last_running_executions = self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user.id,
            "status": "submitted"
        }
        last_running_executions += self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user.id,
            "status": "queued"
        }
        last_running_executions += self.api_endpoint.execution_list(self.current_user, **filters)

        filters = {
            "user_id": self.current_user.id,
            "status": "starting"
        }
        last_running_executions += self.api_endpoint.execution_list(self.current_user, **filters)

        running_reservations = [e.total_reservations for e in last_running_executions if e.total_reservations is not None]
        total_memory = sum([r.memory.min for r in running_reservations])
        total_cores = sum([r.cores.min for r in running_reservations])

        if zoe_lib.config.get_conf().enable_cephfs_quotas:
            try:
                disk_quota = subprocess.check_output(['sudo', '/usr/bin/getfattr', '-n', 'ceph.quota.max_bytes', os.path.join(zoe_lib.config.get_conf().workspace_base_path, zoe_lib.config.get_conf().workspace_deployment_path, self.current_user.username)])
            except subprocess.CalledProcessError:
                disk_quota = -1
                disk_usage = -1
            else:
                disk_quota = int(disk_quota.decode('utf-8').split('=')[1].lstrip('"').strip().rstrip('"'))
                disk_usage = os.stat(os.path.join(zoe_lib.config.get_conf().workspace_base_path, zoe_lib.config.get_conf().workspace_deployment_path, self.current_user.username)).st_size

        else:
            disk_quota = -1
            disk_usage = -1

        template_vars = {
            "total_memory": total_memory,
            "total_cores": total_cores,
            'last_executions': sorted(last_executions, key=lambda e: e.id),
            'running_executions': sorted(last_running_executions, key=lambda e: e.id),
            'disk_quota': disk_quota,
            'disk_usage': disk_usage
        }
        self.render('home_user.jinja2', **template_vars)
