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

"""The Quota API endpoints."""

import tornado.escape

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler
from zoe_api.exceptions import ZoeAuthException


class QuotaAPI(ZoeAPIRequestHandler):
    """The Quota API endpoint. Ops on a single quota."""

    def get(self, quota_id):
        """HTTP GET method."""
        if self.current_user is None:
            return

        quota = self.api_endpoint.quota_by_id(quota_id)
        ret = {
            'quota': quota.serialize()
        }

        self.write(ret)

    def post(self, quota_id):
        """HTTP POST method, to edit a quota."""
        if self.current_user is None:
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            self.set_status(400, 'Error decoding JSON data')
            return

        try:
            self.api_endpoint.quota_update(self.current_user, **data)
        except KeyError:
            self.set_status(400, 'Error decoding JSON data')
            return
        except ZoeAuthException as e:
            self.set_status(401, e.message)
            return

        self.set_status(201)

    def delete(self, quota_id: int):
        """HTTP DELETE method."""
        if self.current_user is None:
            return

        try:
            self.api_endpoint.quota_delete(self.current_user, quota_id)
        except ZoeAuthException as e:
            self.set_status(401, e.message)
            return
        self.set_status(204)


class QuotaCollectionAPI(ZoeAPIRequestHandler):
    """The QuotaCollection API. Ops that interact with the Quota collection."""

    def get(self):
        """HTTP GET method"""
        if self.current_user is None:
            return

        filter_dict = {}

        filters = [
            ('name', str)
        ]
        for filter in filters:
            if filter[0] in self.request.arguments:
                if filter[1] == str:
                    filter_dict[filter[0]] = self.request.arguments[filter[0]][0].decode('utf-8')
                else:
                    filter_dict[filter[0]] = filter[1](self.request.arguments[filter[0]][0])

        try:
            quota = self.api_endpoint.quota_list(self.current_user, **filter_dict)
        except ZoeAuthException as e:
            self.set_status(401, e.message)
            return

        self.write(dict([(r.id, r.serialize()) for r in quota]))

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
            new_id = self.api_endpoint.quota_new(self.current_user, data)
        except KeyError:
            self.set_status(400, 'Error decoding JSON data')
            return
        except ZoeAuthException as e:
            self.set_status(401, e.message)
            return

        self.set_status(201)
        self.write({'quota_id': new_id})
