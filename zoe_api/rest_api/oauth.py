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

"""The oAuth2 API endpoints."""

import logging
import json
import psycopg2

from tornado.web import RequestHandler

import oauth2.grant

from zoe_api.rest_api.utils import catch_exceptions, get_auth
from zoe_api.rest_api.oauth_utils import auth_controller, client_store, token_store
from zoe_api.rest_api.utils import manage_cors_headers
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import

log = logging.getLogger(__name__)

"""

Example of using:

*To request a new token of type:
Input: curl -u 'admin:admin' http://localhost:5001/api/0.6/oauth/token -X POST -H 'Content-Type: application/json' -d '{"grant_type": "password"}'
Output: {"token_type": "Bearer", "access_token": "3ddbe9ba-6a21-4e4d-993b-70556390c5d3", "refresh_token": "9bab190f-e211-42aa-917e-20ce987e355e", "expires_in": 36000}

*To refresh a token
Input: curl  -H 'Authorization: Bearer 9bab190f-e211-42aa-917e-20ce987e355e' http://localhost:5001/api/0.6/oauth/token -X POST -H 'Content-Type: application/json' -d '{"grant_type": "refresh_token"}'
Output: {"token_type": "Bearer", "access_token": "378f8d5f-2eb5-4181-b632-ad23c4534d32", "expires_in": 36000}

*To revoke a token, the passed token could be the access token or refresh token
curl -u 'admin:admin' -X DELETE http://localhost:5001/api/0.6/oauth/revoke/378f8d5f-2eb5-4181-b632-ad23c4534d32

*To authenticate with other rest api services, using a header with: "Authorization: Bearer access_token"
curl -H 'Authorization: Bearer 378f8d5f-2eb5-4181-b632-ad23c4534d32' http://localhost:5001/api/0.6/execution

"""


class OAuthGetAPI(RequestHandler):
    """The OAuthGetAPI endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint
        self.auth_controller = auth_controller
        self.client_store = client_store

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    @catch_exceptions
    def options(self):  # pylint: disable=unused-argument
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def post(self):
        """REQUEST/REFRESH token"""
        uid, role = get_auth(self)

        grant_type = oauth2.grant.RefreshToken.grant_type + ':' + oauth2.grant.ResourceOwnerGrant.grant_type

        try:
            self.client_store.save_client(uid, '', role, '', grant_type, '')
        except psycopg2.IntegrityError:
            log.info('User is already had')

        response = self._dispatch_request(uid)
        self._map_response(response)

    def _dispatch_request(self, uid):
        request = self.request
        params = json.loads(request.body.decode())

        if params['grant_type'] == 'refresh_token':
            auth_header = self.request.headers.get('Authorization')
            refresh_token = auth_header[7:]
            params['refresh_token'] = refresh_token

        params['password'] = ''
        params['username'] = ''
        params['client_secret'] = ''
        params['scope'] = ''
        params['client_id'] = uid

        request.post_param = lambda key: params[key]
        return self.auth_controller.dispatch(request, environ={})

    def _map_response(self, response):
        for name, value in list(response.headers.items()):
            self.set_header(name, value)
        self.set_status(response.status_code)

        if response.status_code == 200:
            log.info("New token granted...")

        self.write(response.body)

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass


class OAuthRevokeAPI(RequestHandler):
    """The OAuthRevokeAPI endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint
        self.auth_controller = auth_controller
        self.token_store = token_store

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    @catch_exceptions
    def options(self, execution_id):  # pylint: disable=unused-argument
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def delete(self, token):
        """DELETE token (logout)"""
        get_auth(self)

        res = self.token_store.delete_refresh_token(token)

        if res == 0:
            ret = {'ret' :'No token found in database.'}
        else:
            ret = {'res': 'Revoked token.'}
        self.write(ret)

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
