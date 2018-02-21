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

"""The Role API endpoints."""

import tornado.escape

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler
from zoe_api.exceptions import ZoeException


class RoleAPI(ZoeAPIRequestHandler):
    """The Role API endpoint. Ops on a single role."""

    def get(self, role_id):
        """HTTP GET method."""
        if self.current_user is None:
            return

        role = self.api_endpoint.role_by_id(role_id)
        ret = {
            'role': role.serialize()
        }

        self.write(ret)

    def post(self, role_id):
        """HTTP POST method, to edit a role."""
        if self.current_user is None:
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            self.set_status(400, 'Error decoding JSON data')
            return

        try:
            self.api_endpoint.role_update(self.current_user, role_id, data)
        except KeyError:
            self.set_status(400, 'Error decoding JSON data')
            return
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.set_status(201)

    def delete(self, role_id: int):
        """HTTP DELETE method."""
        if self.current_user is None:
            return

        try:
            self.api_endpoint.role_delete(self.current_user, role_id)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return
        self.set_status(204)


class RoleCollectionAPI(ZoeAPIRequestHandler):
    """The RoleCollection API. Ops that interact with the Role collection."""

    def get(self):
        """HTTP GET method"""
        if self.current_user is None:
            return

        filter_dict = {}

        filters = [
            ('name', str)
        ]
        for filt in filters:
            if filt[0] in self.request.arguments:
                if filt[1] == str:
                    filter_dict[filt[0]] = self.request.arguments[filt[0]][0].decode('utf-8')
                else:
                    filter_dict[filt[0]] = filt[1](self.request.arguments[filt[0]][0])

        try:
            role = self.api_endpoint.role_list(self.current_user, **filter_dict)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.write(dict([(r.id, r.serialize()) for r in role]))

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
            new_id = self.api_endpoint.role_new(self.current_user, data)
        except KeyError:
            self.set_status(400, 'Error decoding JSON data')
            return
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.set_status(201)
        self.write({'role_id': new_id})
