# Copyright (c) 2016, Quang-Nhat HOANG-XUAN
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

"""Utility functions needed by the Zoe REST API."""

import base64
import logging

from zoe_lib.config import get_conf

from zoe_api.exceptions import ZoeRestAPIException

import tornado.web

import oauth2
import oauth2.tokengenerator
import oauth2.grant
import oauth2.store.redisdb
import oauth2.store.mongodb
import time
import json
import fakeredis
import mongomock

import hashlib
import os
import uuid

log = logging.getLogger(__name__)

class OAuthSiteAdapter(oauth2.web.ResourceOwnerGrantSiteAdapter):
    def authenticate(self, request, environ, scopes, client):
            return {}

class TokenGenerator(object):
    """
    Base class of every token generator.
    """
    def __init__(self):
        """
        Create a new instance of a token generator.
        """
        self.expires_in = {}
        self.refresh_expires_in = 0

    def create_access_token_data(self, grant_type):
        """
        Create data needed by an access token.

        :param grant_type:
        :type grant_type: str

        :return: A ``dict`` containing he ``access_token`` and the
                 ``token_type``. If the value of ``TokenGenerator.expires_in``
                 is larger than 0, a ``refresh_token`` will be generated too.
        :rtype: dict
        """

        if grant_type == 'password':
            self.expires_in['password'] = 36000

        result = {"access_token": self.generate(), "token_type": "Bearer"}

        if self.expires_in.get(grant_type, 0) > 0:
            result["refresh_token"] = self.generate()

            result["expires_in"] = self.expires_in[grant_type]

        return result

    def generate(self):
        """
        Implemented by generators extending this base class.

        :raises NotImplementedError:
        """
        raise NotImplementedError


class URandomTokenGenerator(TokenGenerator):
    """
    Create a token using ``os.urandom()``.
    """
    def __init__(self, length=40):
        self.token_length = length
        TokenGenerator.__init__(self)

    def generate(self):
        """
        :return: A new token
        :rtype: str
        """
        random_data = os.urandom(100)

        hash_gen = hashlib.new("sha512")
        hash_gen.update(random_data)

        return hash_gen.hexdigest()[:self.token_length]


class Uuid4(TokenGenerator):
    """
    Generate a token using uuid4.
    """
    def generate(self):
        """
        :return: A new token
        :rtype: str
        """
        return str(uuid.uuid4())

def get_username_password(handler: tornado.web.RequestHandler):
    """Get username, password"""
    auth_header = handler.request.headers.get('Authorization')

    if auth_header is None or not (auth_header.startswith('Basic ') or auth_header.startswith('Bearer ')):
        raise ZoeRestAPIException('missing or wrong authentication information', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    auth_decoded = base64.decodebytes(bytes(auth_header[6:], 'ascii')).decode('utf-8')

    username, password = auth_decoded.split(':', 2)

    return username, password

mongo = mongomock.MongoClient()
mongo['db']['oauth_clients'].ensure_index("identifier", unique=True)

client_store = oauth2.store.mongodb.ClientStore(mongo['db']['oauth_clients'])
token_store = oauth2.store.redisdb.TokenStore(rs=fakeredis.FakeStrictRedis())

token_generator = Uuid4()
token_generator.expires_in[oauth2.grant.ClientCredentialsGrant.grant_type] = 3600

auth_controller = oauth2.Provider(
    access_token_store=token_store,
    auth_code_store=token_store,
    client_store=client_store,
    token_generator=token_generator
)

site_adapter = OAuthSiteAdapter()

auth_controller.token_path = '/api/0.6/oauth/token'
auth_controller.add_grant(oauth2.grant.ClientCredentialsGrant())
auth_controller.add_grant(oauth2.grant.RefreshToken(expires_in=3600))
auth_controller.add_grant(oauth2.grant.ResourceOwnerGrant(site_adapter=site_adapter))

