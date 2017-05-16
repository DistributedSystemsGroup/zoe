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

"""The Info API endpoint."""

from tornado.web import RequestHandler
import tornado.escape

from zoe_api.rest_api.utils import catch_exceptions, manage_cors_headers
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
import zoe_api.exceptions


class ZAppValidateAPI(RequestHandler):
    """The Info API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    def options(self):
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def post(self):
        """HTTP GET method."""
        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        application_description = data['application']

        self.api_endpoint.zapp_validate(application_description)

        self.write({'validation': 'ok'})

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
