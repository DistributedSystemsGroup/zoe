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

"""Custom request handler for tornado, subclassed to implement authentication."""

import base64
import logging

import tornado.web
import tornado.websocket
import tornado.escape

from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.auth.base import BaseAuthenticator
from zoe_api.exceptions import ZoeAuthException

log = logging.getLogger(__name__)


class ZoeRequestHandler(tornado.web.RequestHandler):
    """Customized request handler."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize()
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def get_current_user(self):
        """Get the user making the request from one of several possible locations."""
        auth_header = self.request.headers.get('Authorization')
        if self.get_secure_cookie('zoe'):  # cookie auth
            username = tornado.escape.xhtml_escape(self.get_secure_cookie('zoe'))
            user = self.api_endpoint.user_by_name(username)
            method = "cookie"
        elif auth_header is not None and auth_header.startswith('Basic '):  # basic auth
            auth_decoded = base64.decodebytes(bytes(auth_header[6:], 'ascii')).decode('utf-8')
            username, password = auth_decoded.split(':', 2)
            user = BaseAuthenticator().full_auth(username, password)
            method = "basic_auth"
        else:
            method = None
            user = None

        if user is None:
            raise ZoeAuthException('Invalid username or password')
        if not user.enabled:
            raise ZoeAuthException('User has been disabled by the administrator')

        log.debug('Authentication done using {} (user {} from {} for {})'.format(method, user.username, self.request.remote_ip, self.request.path))
        return user

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass


class ZoeWSRequestHandler(tornado.websocket.WebSocketHandler):
    """Customized request handler."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize()
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def get_current_user(self):
        """Get the user making the request from one of several possible locations."""
        auth_header = self.request.headers.get('Authorization')
        if self.get_secure_cookie('zoe'):  # cookie auth
            username = tornado.escape.xhtml_escape(self.get_secure_cookie('zoe'))
            user = self.api_endpoint.user_by_name(username)
            method = "cookie"
        elif auth_header is not None and auth_header.startswith('Basic '):  # basic auth
            auth_decoded = base64.decodebytes(bytes(auth_header[6:], 'ascii')).decode('utf-8')
            username, password = auth_decoded.split(':', 2)
            user = BaseAuthenticator().full_auth(username, password)
            method = "basic_auth"
        else:
            method = None
            user = None

        if user is None:
            raise ZoeAuthException('Invalid username or password')
        if not user.enabled:
            raise ZoeAuthException('User has been disabled by the administrator')

        log.debug('Authentication done using {} (user {} from {} for {})'.format(method, user.username, self.request.remote_ip, self.request.path))
        return user

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass

    def on_message(self, message):
        """Must be implemented by a subclass."""
        raise NotImplementedError
