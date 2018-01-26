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

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler
from zoe_api.exceptions import ZoeAuthException


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
            user = self.api_endpoint.user_by_id(self.current_user, user_id)
            ret = {
                'user': user.serialize()
            }

        self.write(ret)

    def post(self, user_id):
        """HTTP POST method."""
        if self.current_user is None:
            return

    def delete(self, user_id: int):
        """HTTP DELETE method."""
        if self.current_user is None:
            return

        try:
            self.api_endpoint.user_delete(self.current_user, user_id)
        except ZoeAuthException as e:
            self.set_status(401, e.message)
        self.set_status(204)


class UserCollectionAPI(ZoeAPIRequestHandler):
    """The UserCollection API. Ops that interact with the User collection."""

    def get(self):
        """HTTP GET method"""
        if self.current_user is None:
            return

    def post(self):
        """HTTP POST method."""
        if self.current_user is None:
            return
