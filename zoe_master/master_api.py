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

import logging
import time

import zmq

from zoe_lib.exceptions import ZoeException
from zoe_master.config import get_conf, singletons

log = logging.getLogger(__name__)


class APIManager:
    def __init__(self):
        context = zmq.Context()
        self.zmq_s = context.socket(zmq.REP)
        self.listen_uri = get_conf().api_listen_uri
        self.zmq_s.bind(self.listen_uri)
        self.debug_has_replied = False

    def _reply_error(self, message):
        self.zmq_s.send_json({'result': 'error', 'message': message})
        self.debug_has_replied = True

    def _reply_ok(self):
        self.zmq_s.send_json({'result': 'ok'})
        self.debug_has_replied = True

    def loop(self):
        while True:
            message = self.zmq_s.recv_json()
            self.debug_has_replied = False
            start_time = time.time()
            if message['command'] == 'execution_start':
                exec_id = message['exec_id']
                execution = singletons['sql_manager'].execution_get(id=exec_id)
                if execution is None:
                    self._reply_error('Execution ID {} not found'.format(message['exec_id']))
                else:
                    self._reply_ok()
                    singletons['platform_manager'].execution_submit(execution)
            else:
                log.error('Unknown command: {}'.format(message['command']))
                self._reply_error('unknown command')

            if not self.debug_has_replied:
                self._reply_error('bug')
                raise ZoeException('BUG: command {} does not fill a reply')

            singletons['metric'].metric_api_call(start_time, message['command'])
