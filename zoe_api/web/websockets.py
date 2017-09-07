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

"""Ajax API for the Zoe web interface."""

import datetime
import json
import logging

import tornado.websocket
import tornado.iostream
from tornado.web import asynchronous


from zoe_lib.config import get_conf
import zoe_api.exceptions
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.utils import get_auth, catch_exceptions

log = logging.getLogger(__name__)


class WebSocketEndpointWeb(tornado.websocket.WebSocketHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize()
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint
        self.uid = None
        self.role = None
        self.log_obj = None
        self.stream = None

    @catch_exceptions
    def open(self, *args, **kwargs):
        """Invoked when a new WebSocket is opened."""
        log.debug('WebSocket opened')
        uid, role = get_auth(self)
        if uid is None:
            self.close(401, "Unauthorized")
        else:
            self.uid = uid
            self.role = role

    @catch_exceptions
    @asynchronous
    def on_message(self, message):
        """WebSocket message handler."""

        if message is None:
            return

        request = json.loads(message)

        if request['command'] == 'start_zapp':
            app_descr = json.load(open('contrib/zoeapps/eurecom_aml_lab.json', 'r'))
            execution = self.api_endpoint.execution_list(self.uid, self.role, name='aml-lab')
            if len(execution) == 0:
                exec_id = self.api_endpoint.execution_start(self.uid, self.role, 'aml-lab', app_descr)
            else:
                execution = execution[0]
                exec_id = execution.id
            response = {
                'status': 'ok',
                'execution_id': exec_id
            }
            self.write_message(response)
        elif request['command'] == 'query_status':
            try:
                execution = self.api_endpoint.execution_by_id(self.uid, self.role, request['exec_id'])
            except zoe_api.exceptions.ZoeNotFoundException:
                response = {
                    'status': 'ok',
                    'exec_status': 'none'
                }
            else:
                response = {
                    'status': 'ok',
                    'exec_status': execution.status
                }
                if execution.status == execution.RUNNING_STATUS:
                    response['ttl'] = ((execution.time_start + datetime.timedelta(hours=get_conf().aml_ttl)) - datetime.datetime.now()).total_seconds()
                    services_info_, endpoints = self.api_endpoint.execution_endpoints(self.uid, self.role, execution)
                    response['endpoints'] = endpoints
                elif execution.status == execution.ERROR_STATUS or execution.status == execution.TERMINATED_STATUS:
                    self.api_endpoint.execution_delete(self.uid, self.role, execution.id)
                self.write_message(response)
        elif request['command'] == 'service_logs':
            self.log_obj = self.api_endpoint.service_logs(self.uid, self.role, request['service_id'], stream=True)
            self.stream = tornado.iostream.PipeIOStream(self.log_obj.fileno())
            self.stream.read_until(b'\n', callback=self._stream_log_line)
        else:
            response = {
                'status': 'error',
                'message': 'unknown request type'
            }
            self.write_message(response)

    def _stream_log_line(self, log_line):
        self.write_message(log_line)
        self.stream.read_until(b'\n', callback=self._stream_log_line)

    def on_close(self):
        """Invoked when the WebSocket is closed."""
        log.debug("WebSocket closed")

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
