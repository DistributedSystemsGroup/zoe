# Copyright (c) 2017, Daniele Venzano, Quang-Nhat Hoang-Xuan
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

"""The User API endpoint."""

import tornado.escape

from zoe_api.rest_api.utils import catch_exceptions, needs_auth
import zoe_api.exceptions
from zoe_api.rest_api.custom_request_handler import BaseRequestHandler


class LoginAPI(BaseRequestHandler):
    """The Login API endpoint."""

    @catch_exceptions
    @needs_auth
    def get(self):
        """HTTP GET method."""
        self.set_secure_cookie('zoe_api_user', self.current_user.username)

        ret = {
            'uid': self.current_user.username,
            'role': self.current_user.role
        }

        self.write(ret)


class UserCollectionAPI(BaseRequestHandler):
    """The User collection API endpoint."""

    @catch_exceptions
    @needs_auth
    def get(self):
        """HTTP GET method."""
        filt_dict = {}
        users = self.api_endpoint.user_list(self.current_user, **filt_dict)

        self.write(dict([(u.id, u.serialize()) for u in users]))


class UserAPI(BaseRequestHandler):
    """The Login API endpoint."""

    @catch_exceptions
    @needs_auth
    def get(self, user_name):
        """HTTP GET method."""
        if self.current_user.role != "admin" and self.current_user.username != user_name:
            raise zoe_api.exceptions.ZoeAuthException('Unauthorized access')

        user = self.api_endpoint.user_identify(user_name)

        self.write(user.serialize())

    @catch_exceptions
    @needs_auth
    def put(self, user_name):
        """Update user information"""
        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        self.api_endpoint.user_update(self.current_user, user_name, data)
