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

import logging

from tornado.web import RequestHandler
import tornado.gen

from zoe_api.rest_api.utils import catch_exceptions, get_auth
from zoe_api.api_endpoint import APIEndpoint

log = logging.getLogger(__name__)


class ServiceAPI(RequestHandler):
    """The Service API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, service_id) -> dict:
        """HTTP GET method."""
        uid, role = get_auth(self)

        service = self.api_endpoint.service_by_id(uid, role, service_id)

        self.write(service.serialize())


class ServiceLogsAPI(RequestHandler):
    """The Service logs API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint
        self.connection_closed = False

    def on_connection_close(self):
        """Tornado callback for clients closing the connection."""
        self.connection_closed = True

    @catch_exceptions
    @tornado.gen.engine
    def get(self, service_id) -> dict:
        """HTTP GET method."""

        def cb(callback):
            if self.connection_closed:
                tmp_line = None
            else:
                tmp_line = next(log_gen)
            callback(tmp_line)

        uid, role = get_auth(self)

        log_gen = self.api_endpoint.service_logs(uid, role, service_id, stream=True)

        while True:
            log_line = yield tornado.gen.Task(cb)
            if log_line is None:
                break
            else:
                self.write(log_line)
                yield self.flush()

        self.finish()
