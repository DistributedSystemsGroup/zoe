# Copyright (c) 2017, Quang-Nhat HOANG-XUAN
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

"""Authentication controller for oauth2."""

import logging
import oauth2.web
import oauth2.grant

from zoe_api.auth.oauth2.postgresql import AccessTokenStorePg, ClientStorePg
from zoe_api.auth.oauth2.tokengenerator import Uuid4

log = logging.getLogger(__name__)

class OAuthSiteAdapter(oauth2.web.ResourceOwnerGrantSiteAdapter):
    """OAuth Simple SiteAdapter"""
    def authenticate(self, request, environ, scopes, client):
        return {}

client_store = ClientStorePg() #pylint: disable=invalid-name
token_store = AccessTokenStorePg() #pylint: disable=invalid-name

token_generator = Uuid4() #pylint: disable=invalid-name
token_generator.expires_in[oauth2.grant.ClientCredentialsGrant.grant_type] = 3600

auth_controller = oauth2.Provider( #pylint: disable=invalid-name
    access_token_store=token_store,
    auth_code_store=token_store,
    client_store=client_store,
    token_generator=token_generator
)

site_adapter = OAuthSiteAdapter() #pylint: disable=invalid-name

auth_controller.token_path = '/api/0.7/oauth/token'
auth_controller.add_grant(oauth2.grant.ClientCredentialsGrant())
auth_controller.add_grant(oauth2.grant.RefreshToken(expires_in=3600))
auth_controller.add_grant(oauth2.grant.ResourceOwnerGrant(site_adapter=site_adapter))
