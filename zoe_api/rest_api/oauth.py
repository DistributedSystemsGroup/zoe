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

"""The Execution API endpoints."""

from tornado.web import RequestHandler
import tornado.escape

import logging

import zoe_lib.config as config
from zoe_api.rest_api.utils import catch_exceptions, get_auth
from zoe_api.rest_api.oauth_utils import auth_controller, mongo, get_username_password
import zoe_api.exceptions
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import

import oauth2.grant

import json
import requests
import pymongo

log = logging.getLogger(__name__)

"""

Example of using:

-Two kind of request token:
(1) with an access token and a refresh token
(2) with only an access token

*To request a new token of type:

(1):
Input: curl -u 'admin:admin' http://localhost:5001/api/0.6/oauth/token -X POST -H 'Content-Type: application/json' -d '{"client_id": "admin", "client_secret": "admin", "grant_type": "password", "username": "admin", "password": "admin", "scope": ""}'
Output: {"token_type": "Bearer", "access_token": "3ddbe9ba-6a21-4e4d-993b-70556390c5d3", "refresh_token": "9bab190f-e211-42aa-917e-20ce987e355e", "expires_in": 36000}

(2): 
Input: curl -u 'admin:admin' http://localhost:5001/api/0.6/oauth/token -X POST -H 'Content-Type: application/json' -d '{"client_id": "admin", "client_secret": "admin", "grant_type": "client_credentials", "scope": ""}'
Output: {"token_type": "Bearer", "access_token": "e6ab7c66-777b-4b64-91e0-2f501d28fe6e", "expires_in": 3600}

*To refresh a token, only apply for type-1 request token
Input: curl -u 'admin:admin' http://localhost:5001/api/0.6/oauth/token -X POST -H 'Content-Type: application/json' -d '{"client_id": "admin", "client_secret": "admin", "grant_type": "refresh_token", "refresh_token": "9bab190f-e211-42aa-917e-20ce987e355e", "username": "admin", "password": "admin", "scope": ""}'
Output: {"token_type": "Bearer", "access_token": "378f8d5f-2eb5-4181-b632-ad23c4534d32", "expires_in": 36000}

*To revoke a token, apply for two types of token requested
curl -i --verbose -u 'admin:admin' -X DELETE http://localhost:5001/api/0.6/oauth/revoke/e6ab7c66-777b-4b64-91e0-2f501d28fe6e

*To authenticate with other rest api services, using a header with: "Authorization: Bearer access_token"
curl -H 'Authorization: Bearer 378f8d5f-2eb5-4181-b632-ad23c4534d32' http://localhost:5001/api/0.6/execution

"""

class OAuthGetAPI(RequestHandler):
    """The OAuthGetAPI endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint
        self.auth_controller = auth_controller
        self.mongo = mongo

    @catch_exceptions
    def post(self):
        """REQUEST/REFRESH token"""
        username, password = get_username_password(self)

        uid, role = get_auth(self)
        
        try:
            self.mongo['db']['oauth_clients'].insert(
            {'identifier': username,
             'secret': password,
             'redirect_uris': [],
             'authorized_grants': [ oauth2.grant.RefreshToken.grant_type,
                                    oauth2.grant.ResourceOwnerGrant.grant_type,
                                    oauth2.grant.ClientCredentialsGrant.grant_type]})
        
        except pymongo.errors.DuplicateKeyError as e:
            log.warn("Already had this user in db, skip adding...")
        
        response = self._dispatch_request()
        self._map_response(response)

    def _dispatch_request(self):
        request = self.request
        request.post_param = lambda key: json.loads(request.body.decode())[key]
        return self.auth_controller.dispatch(request, environ={})
    
    def _map_response(self, response):
        for name, value in list(response.headers.items()):
            self.set_header(name, value)
        self.set_status(response.status_code)

        if response.status_code == 200:
            log.info("New token granted...")

        self.write(response.body)

    def data_received(self, chunk):
        pass

class OAuthRevokeAPI(RequestHandler):

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint
        self.auth_controller = auth_controller

    @catch_exceptions
    def delete(self, token):
        """DELETE token (logout)"""
        uid, role = get_auth(self)
        
        key = 'oauth2_{}'.format(token)
        res = self.auth_controller.access_token_store.rs.delete(key)

        if res == 0:
            raise zoe_api.exceptions.ZoeRestAPIException('No token found in database')
       
        ret = {'res': 'Revoked token.'}
        self.write(ret)
