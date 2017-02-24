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

"""Master side of the ZeroMQ based API."""

import logging
import time

import zmq

import zoe_lib.config as config
from zoe_lib.metrics.base import BaseMetricSender
from zoe_lib.state import SQLManager

import zoe_master.preprocessing
from zoe_master.exceptions import ZoeException
from zoe_master.scheduler import ZoeBaseScheduler

log = logging.getLogger(__name__)


class APIManager:
    """The API Manager."""
    def __init__(self, metrics: BaseMetricSender, scheduler: ZoeBaseScheduler, state: SQLManager) -> None:
        self.context = zmq.Context()
        self.zmq_s = self.context.socket(zmq.REP)
        self.listen_uri = config.get_conf().api_listen_uri
        self.zmq_s.bind(self.listen_uri)
        self.debug_has_replied = False
        self.metrics = metrics
        self.scheduler = scheduler
        self.state = state

    def _reply_error(self, message: str) -> None:
        self.zmq_s.send_json({'result': 'error', 'message': message})
        self.debug_has_replied = True

    def _reply_ok(self, data=None):
        reply = {
            'result': 'ok'
        }
        if data is not None:
            reply['data'] = data
        self.zmq_s.send_json(reply)
        self.debug_has_replied = True

    def loop(self):
        """The API loop."""
        while True:
            message = self.zmq_s.recv_json()
            self.debug_has_replied = False
            start_time = time.time()
            if message['command'] == 'execution_start':
                exec_id = message['exec_id']
                execution = self.state.execution_list(id=exec_id, only_one=True)
                if execution is None:
                    self._reply_error('Execution ID {} not found'.format(message['exec_id']))
                else:
                    execution.set_scheduled()
                    self._reply_ok()
                    zoe_master.preprocessing.execution_submit(self.state, self.scheduler, execution)
            elif message['command'] == 'execution_terminate':
                exec_id = message['exec_id']
                execution = self.state.execution_list(id=exec_id, only_one=True)
                if execution is None:
                    self._reply_error('Execution ID {} not found'.format(message['exec_id']))
                else:
                    execution.set_cleaning_up()
                    self._reply_ok()
                    zoe_master.preprocessing.execution_terminate(self.scheduler, execution)
            elif message['command'] == 'execution_delete':
                exec_id = message['exec_id']
                execution = self.state.execution_list(id=exec_id, only_one=True)
                if execution is not None:
                    zoe_master.preprocessing.execution_delete(execution)
                self._reply_ok()
            elif message['command'] == 'scheduler_stats':
                data = self.scheduler.stats()
                self._reply_ok(data=data)
            else:
                log.error('Unknown command: {}'.format(message['command']))
                self._reply_error('unknown command')

            if not self.debug_has_replied:
                self._reply_error('bug')
                raise ZoeException('BUG: command {} does not fill a reply')

            self.metrics.metric_api_call(start_time, message['command'])

    def quit(self) -> None:
        """Cleanly close the ZMQ resources."""
        self.zmq_s.close()
        self.context.term()
