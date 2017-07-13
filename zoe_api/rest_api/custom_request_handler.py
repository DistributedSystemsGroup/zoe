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

"""Customized Tornado request handler for the Zoe REST API."""

import logging
from typing import Union

from tornado.web import RequestHandler

from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.rest_api.utils import try_basic_auth
import zoe_api.exceptions
from zoe_lib.state import User

log = logging.getLogger(__name__)


class BaseRequestHandler(RequestHandler):
    """Customized Tornado request handler for the Zoe REST API."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = self.application.api_endpoint  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        if self.request.headers.get('Origin') is None:
            self.set_header("Access-Control-Allow-Origin", "*")
        else:
            self.set_header("Access-Control-Allow-Origin", self.request.headers.get('Origin'))
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type, origin, authorization, accept, client-security-token")
        self.set_header("Access-Control-Allow-Methods", "OPTIONS, GET, DELETE")
        self.set_header("Access-Control-Max-Age", "1000")

    def options(self):
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass

    def _uid_to_user(self, uid: str) -> Union[User, None]:
        try:
            return self.application.api_endpoint.user_identify(uid)
        except zoe_api.exceptions.ZoeNotFoundException:
            return None

    def get_current_user(self) -> Union[User, None]:
        """Authenticate each request."""
        if self.get_secure_cookie('zoe_web_user'):
            uid = self.get_secure_cookie('zoe').decode('uft-8')
            log.info('Authentication done using cookie')
            return self._uid_to_user(uid)

        auth_header = self.request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Basic '):
            return None

        try:
            uid, role = try_basic_auth(self)
        except zoe_api.exceptions.ZoeAuthException:
            return None

        log.debug('Authentication done using auth-mechanism')
        user = self._uid_to_user(uid)
        if user is None:
            self.api_endpoint.user_new(uid, role)
            log.info('New user created: {}'.format(uid))
            user = self._uid_to_user(uid)

        if not user.enabled:
            return None
        if user.role != role:
            log.info('Role for user {} updated, set to {}'.format(user.username, user.role))
            user.set_role(role)

        return user
