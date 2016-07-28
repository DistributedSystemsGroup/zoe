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
import tornado.gen
import tornado.iostream

from zoe_api.rest_api.utils import catch_exceptions, get_auth
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import

log = logging.getLogger(__name__)

thread_pool = ThreadPoolExecutor(20)


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

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass


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
    @tornado.gen.coroutine
    def get(self, service_id):
        """HTTP GET method."""

        uid, role = get_auth(self)

        log_gen = self.api_endpoint.service_logs(uid, role, service_id, stream=True)

        while True:
            try:
                log_line = yield thread_pool.submit(next, log_gen)
            except StopIteration:
                break

            self.write(log_line)

            try:
                yield self.flush()
            except tornado.iostream.StreamClosedError:
                break

            if self.connection_closed:
                break

        log.debug('Finished log stream for service {}'.format(service_id))
        self.finish()

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
