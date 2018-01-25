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

import tornado.gen
import tornado.iostream

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler

log = logging.getLogger(__name__)

THREAD_POOL = ThreadPoolExecutor(20)


class ServiceAPI(ZoeAPIRequestHandler):
    """The Service API endpoint."""

    def get(self, service_id):
        """HTTP GET method."""
        if self.current_user is None:
            return

        service = self.api_endpoint.service_by_id(self.current_user, service_id)

        self.write(service.serialize())


class ServiceLogsAPI(ZoeAPIRequestHandler):
    """The Service logs API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.connection_closed = False
        self.service_id = None
        self.stream = None
        self.log_obj = None

    def on_connection_close(self):
        """Tornado callback for clients closing the connection."""
        log.debug('Finished log stream for service {}'.format(self.service_id))
        self.connection_closed = True
        self.finish()

    @tornado.gen.coroutine
    def get(self, service_id):
        """HTTP GET method."""
        if self.current_user is None:
            return

        log_obj = self.api_endpoint.service_logs(self.current_user, service_id)

        while not self.connection_closed:
            try:
                log_line = yield THREAD_POOL.submit(next, log_obj)
            except StopIteration:
                yield tornado.gen.sleep(0.2)
                continue

            self.write(log_line)

            try:
                yield self.flush()
            except tornado.iostream.StreamClosedError:
                break
