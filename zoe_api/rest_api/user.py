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

"""The User API endpoints."""

import logging
import os

import requests
import tornado.escape

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler
from zoe_api.exceptions import ZoeException
from zoe_api.auth.requests_oauth2 import EurecomGitLabClient

import zoe_lib.config

log = logging.getLogger(__name__)


class UserAPI(ZoeAPIRequestHandler):
    """The User API endpoint. Ops on a single user."""

    def get(self, user_id):
        """HTTP GET method."""
        if self.current_user is None:
            return

        if user_id == self.current_user.id:
            ret = {
                'user': self.current_user.serialize()
            }
        else:
            try:
                user = self.api_endpoint.user_by_id(self.current_user, user_id)
            except ZoeException as e:
                self.set_status(e.status_code, e.message)
                return
            ret = {
                'user': user.serialize()
            }

        self.write(ret)

    def post(self, user_id):
        """HTTP POST method, to edit a user."""
        if self.current_user is None:
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            self.set_status(400, 'Error decoding JSON data')
            return

        try:
            self.api_endpoint.user_update(self.current_user, user_id, data)
        except KeyError:
            self.set_status(400, 'Error decoding JSON data')
            return
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.set_status(201)

    def delete(self, user_id: int):
        """HTTP DELETE method."""
        if self.current_user is None:
            return

        try:
            self.api_endpoint.user_delete(self.current_user, user_id)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return
        self.set_status(204)


class UserCollectionAPI(ZoeAPIRequestHandler):
    """The UserCollection API. Ops that interact with the User collection."""

    def get(self):
        """HTTP GET method"""
        if self.current_user is None:
            return

        filter_dict = {}

        filters = [
            ('username', str),
            ('email', str),
            ('priority', int),
            ('enabled', bool),
            ('auth_source', str),
            ('role_id', int),
            ('quota_id', int)
        ]
        for filt in filters:
            if filt[0] in self.request.arguments:
                if filt[1] == str:
                    filter_dict[filt[0]] = self.request.arguments[filt[0]][0].decode('utf-8')
                if filt[1] == bool:
                    text_val = self.request.arguments[filt[0]][0].decode('utf-8')
                    if text_val == 'False':
                        filter_dict[filt[0]] = False
                    elif text_val == 'True':
                        filter_dict[filt[0]] = True
                else:
                    filter_dict[filt[0]] = filt[1](self.request.arguments[filt[0]][0])

        try:
            users = self.api_endpoint.user_list(self.current_user, **filter_dict)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.write({u.id: u.serialize() for u in users})

    def post(self):
        """HTTP POST method."""
        if self.current_user is None:
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            self.set_status(400, 'Error decoding JSON data')
            return

        try:
            new_id = self.api_endpoint.user_new(self.current_user, data['username'], data['email'], data['role_id'], data['quota_id'], data['auth_source'], data['fs_uid'])
        except KeyError:
            self.set_status(400, 'Error decoding JSON data')
            return
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.set_status(201)
        self.write({'user_id': new_id})


class UserOAuthCallbackAPI(ZoeAPIRequestHandler):
    """The User OAUTH callback endpoint."""
    def get(self):
        """Callback."""
        code = self.get_argument('code', None)
        if code is None:
            self.redirect(self.reverse_url("login"))
            return

        egitlab = EurecomGitLabClient(client_id=zoe_lib.config.get_conf().oauth_client_id, client_secret=zoe_lib.config.get_conf().oauth_client_secret, redirect_uri=zoe_lib.config.get_conf().oauth_redirect_uri)
        token = egitlab.get_token(code=code, grant_type="authorization_code")
        resp = requests.get(egitlab.userinfo_url, headers={'Authorization': 'Bearer {}'.format(token['access_token'])})
        if resp.status_code != 200:
            self.redirect(self.reverse_url("login"))
            return
        data = resp.json()
        try:
            email = data['email']
        except KeyError:
            with_gitlab_oauth = zoe_lib.config.get_conf().oauth_client_id != ''
            self.render('login.jinja2', error='Email address not set to public in GitLab settings', with_gitlab_oauth=with_gitlab_oauth)
            return
        username = data['nickname']
        user = self.api_endpoint.user_by_name(username)
        if user is not None:
            if user.email != email:
                self.api_endpoint.user_update(user, user.id, {'email': email})
        else:
            log.info('Creating new user {} from OAuth login'.format(username))
            admin = self.api_endpoint.user_by_name('admin')
            role = self.api_endpoint.role_by_name(zoe_lib.config.get_conf().oauth_role)
            quota = self.api_endpoint.quota_by_name(zoe_lib.config.get_conf().oauth_quota)
            self.api_endpoint.user_new(admin, username, email, role.id, quota.id, 'gitlab-eurecom', -1)
            user = self.api_endpoint.user_by_name(username)
            os.system('sudo {} {} {}'.format(zoe_lib.config.get_conf().oauth_create_workspace_script, user.username, user.fs_uid))
        if not self.get_secure_cookie('zoe'):
            cookie_val = user.username
            self.set_secure_cookie('zoe', cookie_val)
        self.redirect(self.get_argument("next", self.reverse_url("home_user")))
