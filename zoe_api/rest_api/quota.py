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

from tornado.web import RequestHandler
import tornado.escape

from zoe_api.rest_api.utils import get_auth, catch_exceptions, manage_cors_headers
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
import zoe_api.exceptions


class QuotaAPI(RequestHandler):
    """The Quota API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    @catch_exceptions
    def options(self):
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass

    @catch_exceptions
    def get(self, quota_id):
        """Get one quota object."""
        uid, role = get_auth(self)

        quota = self.api_endpoint.quota_by_id(uid, role, quota_id)

        self.write(quota.serialize())

    @catch_exceptions
    def put(self, quota_id):
        """Update a quota object."""
        uid, role = get_auth(self)

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        self.api_endpoint.quota_update(uid, role, quota_id, data)

        self.set_status(204)

    @catch_exceptions
    def delete(self, quota_id):
        """Delete a quota."""
        uid, role = get_auth(self)

        self.api_endpoint.quota_delete(uid, role, quota_id)

        self.set_status(204)


class QuotaCollectionAPI(RequestHandler):
    """The Quota API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    @catch_exceptions
    def options(self):
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass

    @catch_exceptions
    def get(self):
        """Retrieve a possibly filtered list of quotas."""
        uid, role = get_auth(self)

        filt_dict = {}
        quotas = self.api_endpoint.quota_list(uid, role, **filt_dict)

        self.write(dict([(q.id, q.serialize()) for q in quotas]))

    @catch_exceptions
    def post(self):
        """
        Creates a new quota. Takes a JSON object.

        :return: the new quota_id
        """
        uid, role = get_auth(self)

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        name = data['name']
        cc_exec = int(data['cc_exec'])
        memory = int(data['memory'])
        cores = int(data['cores'])

        new_id = self.api_endpoint.quota_new(uid, role, name, cc_exec, memory, cores)

        self.set_status(201)
        self.write({'quota_id': new_id})
