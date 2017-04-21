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

""" Store adapters to read/write data to from/to PostgresSQL. """

import zoe_lib.state

from zoe_lib.config import get_conf
from oauth2.store import AccessTokenStore, ClientStore
from oauth2.datatype import AccessToken, Client
from oauth2.error import AccessTokenNotFound, ClientNotFoundError

class AccessTokenStorePg(AccessTokenStore):
    """ AccessTokenStore for postgresql  """

    def fetch_by_refresh_token(self, refresh_token):
        """ get accesstoken from refreshtoken """
        sql = zoe_lib.state.SQLManager(get_conf())
        data = sql.fetch_by_refresh_token(refresh_token)

        if data is None:
            raise AccessTokenNotFound

        return AccessToken(client_id=data["client_id"],
                           grant_type=data["grant_type"],
                           token=data["token"],
                           data=data["data"],
                           expires_at=data["expires_at"].timestamp(),
                           refresh_token=data["refresh_token"],
                           refresh_expires_at=data["refresh_token_expires_at"].timestamp(),
                           scopes=data["scopes"])

    def delete_refresh_token(self, refresh_token):
        """
        Deletes (invalidates) an old refresh token after use
        :param refresh_token: The refresh token.
        """
        sql = zoe_lib.state.SQLManager(get_conf())
        res = sql.delete_refresh_token(refresh_token)
        return res

    def get_client_id_by_refresh_token(self, refresh_token):
        """ get clientID from refreshtoken """
        sql = zoe_lib.state.SQLManager(get_conf())
        data = sql.get_client_id_by_refresh_token(refresh_token)

        return data

    def get_client_id_by_access_token(self, access_token):
        """ get clientID from accesstoken """
        sql = zoe_lib.state.SQLManager(get_conf())
        data = sql.get_client_id_by_access_token(access_token)

        return data

    def fetch_existing_token_of_user(self, client_id, grant_type, user_id):
        """ get accesstoken from userid """
        sql = zoe_lib.state.SQLManager(get_conf())
        data = sql.fetch_existing_token_of_user(client_id, grant_type, user_id)

        if data is None:
            raise AccessTokenNotFound

        return AccessToken(client_id=data["client_id"],
                           grant_type=data["grant_type"],
                           token=data["token"],
                           data=data["data"],
                           expires_at=data["expires_at"].timestamp(),
                           refresh_token=data["refresh_token"],
                           refresh_expires_at=data["refresh_token_expires_at"].timestamp(),
                           scopes=data["scopes"],
                           user_id=data["user_id"])

    def save_token(self, access_token):
        """ save accesstoken """
        sql = zoe_lib.state.SQLManager(get_conf())
        sql.save_token(access_token.client_id,
                       access_token.grant_type,
                       access_token.token,
                       access_token.data,
                       access_token.expires_at,
                       access_token.refresh_token,
                       access_token.refresh_expires_at,
                       access_token.scopes,
                       access_token.user_id)

        return True


class ClientStorePg(ClientStore):
    """ ClientStore for postgres """

    def save_client(self, identifier, secret, role, redirect_uris, authorized_grants, authorized_response_types):
        """ save client to db """
        sql = zoe_lib.state.SQLManager(get_conf())
        sql.save_client(identifier,
                        secret,
                        role,
                        redirect_uris,
                        authorized_grants,
                        authorized_response_types)
        return True

    def fetch_by_client_id(self, client_id):
        """ get client by clientid """
        sql = zoe_lib.state.SQLManager(get_conf())
        client_data = sql.fetch_by_client_id(client_id)

        client_data_grants = client_data["authorized_grants"].split(':')

        if client_data is None:
            raise ClientNotFoundError

        return Client(identifier=client_data["identifier"],
                      secret=client_data["secret"],
                      redirect_uris=client_data["redirect_uris"],
                      authorized_grants=client_data_grants,
                      authorized_response_types=client_data["authorized_response_types"])

    def get_role_by_client_id(self, client_id):
        """ get client role by clientid """
        sql = zoe_lib.state.SQLManager(get_conf())
        client_data = sql.fetch_by_client_id(client_id)

        if client_data is None:
            raise ClientNotFoundError

        return client_data["role"]
