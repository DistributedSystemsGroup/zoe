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

"""The Quota API endpoint."""

import tornado.escape

from zoe_api.rest_api.utils import catch_exceptions, needs_auth
import zoe_api.exceptions
from zoe_api.rest_api.custom_request_handler import BaseRequestHandler


class QuotaAPI(BaseRequestHandler):
    """The Quota API endpoint."""

    @catch_exceptions
    @needs_auth
    def get(self, quota_id):
        """Get one quota object."""
        quota = self.api_endpoint.quota_by_id(self.current_user, quota_id)

        self.write(quota.serialize())

    @catch_exceptions
    @needs_auth
    def put(self, quota_id):
        """Update a quota object."""
        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        self.api_endpoint.quota_update(self.current_user, quota_id, data)

        self.set_status(204)

    @catch_exceptions
    @needs_auth
    def delete(self, quota_id):
        """Delete a quota."""
        self.api_endpoint.quota_delete(self.current_user, quota_id)

        self.set_status(204)


class QuotaCollectionAPI(BaseRequestHandler):
    """The Quota API endpoint."""

    @catch_exceptions
    @needs_auth
    def get(self):
        """Retrieve a possibly filtered list of quotas."""
        filt_dict = {}
        quotas = self.api_endpoint.quota_list(self.current_user, **filt_dict)

        self.write(dict([(q.id, q.serialize()) for q in quotas]))

    @catch_exceptions
    @needs_auth
    def post(self):
        """
        Creates a new quota. Takes a JSON object.

        :return: the new quota_id
        """
        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        name = data['name']
        cc_exec = int(data['cc_exec'])
        memory = int(data['memory'])
        cores = int(data['cores'])

        new_id = self.api_endpoint.quota_new(self.current_user, name, cc_exec, memory, cores)

        self.set_status(201)
        self.write({'quota_id': new_id})
