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

"""The Info API endpoint."""

from tornado.web import RequestHandler

from zoe_api.rest_api.utils import catch_exceptions
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import

from zoe_lib.config import get_conf
from zoe_lib.version import ZOE_API_VERSION, ZOE_APPLICATION_FORMAT_VERSION, ZOE_VERSION


class InfoAPI(RequestHandler):
    """The Info API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint
        
    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        if self.request.headers.get is None:
            self.set_header("Access-Control-Allow-Origin", "*")
        else:
            self.set_header("Access-Control-Allow-Origin", self.request.headers.get('Origin'))
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type, origin, authorization, accept, client-security-token")
        self.set_header("Access-Control-Allow-Methods", "OPTIONS, GET")
        self.set_header("Access-Control-Max-Age", "1000")
        
    def options(self):
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def get(self):
        """HTTP GET method."""
        ret = {
            'version': ZOE_VERSION,
            'api_version': ZOE_API_VERSION,
            'application_format_version': ZOE_APPLICATION_FORMAT_VERSION,
            'deployment_name': get_conf().deployment_name
        }

        self.write(ret)

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
