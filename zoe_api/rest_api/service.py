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

"""The Service API endpoint."""

from concurrent.futures import ThreadPoolExecutor
import logging

from tornado.web import RequestHandler

from zoe_api.rest_api.utils import catch_exceptions, get_auth, manage_cors_headers
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import

log = logging.getLogger(__name__)

THREAD_POOL = ThreadPoolExecutor(20)


class ServiceAPI(RequestHandler):
    """The Service API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    @catch_exceptions
    def options(self, service_id): # pylint: disable=unused-argument
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def get(self, service_id):
        """HTTP GET method."""
        uid, role = get_auth(self)

        service = self.api_endpoint.service_by_id(uid, role, service_id)

        self.write(service.serialize())

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
