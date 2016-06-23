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

from zoe_master.exceptions import ZoeException
import zoe_lib.sql_manager
from zoe_lib.swarm_client import SwarmClient

import zoe_master.config as config
import zoe_master.execution_manager

log = logging.getLogger(__name__)


class APIManager:
    def __init__(self):
        self.context = zmq.Context()
        self.zmq_s = self.context.socket(zmq.REP)
        self.listen_uri = config.get_conf().api_listen_uri
        self.zmq_s.bind(self.listen_uri)
        self.debug_has_replied = False

    def _reply_error(self, message):
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
        assert isinstance(config.singletons['sql_manager'], zoe_lib.sql_manager.SQLManager)
        while True:
            message = self.zmq_s.recv_json()
            self.debug_has_replied = False
            start_time = time.time()
            if message['command'] == 'execution_start':
                exec_id = message['exec_id']
                execution = config.singletons['sql_manager'].execution_list(id=exec_id, only_one=True)
                if execution is None:
                    self._reply_error('Execution ID {} not found'.format(message['exec_id']))
                else:
                    execution.set_scheduled()
                    self._reply_ok()
                    zoe_master.execution_manager.execution_submit(execution)
            elif message['command'] == 'execution_terminate':
                exec_id = message['exec_id']
                execution = config.singletons['sql_manager'].execution_list(id=exec_id, only_one=True)
                if execution is None:
                    self._reply_error('Execution ID {} not found'.format(message['exec_id']))
                else:
                    execution.set_cleaning_up()
                    self._reply_ok()
                    zoe_master.execution_manager.execution_terminate(execution)
            elif message['command'] == 'execution_delete':
                exec_id = message['exec_id']
                execution = config.singletons['sql_manager'].execution_list(id=exec_id, only_one=True)
                if execution is not None:
                    zoe_master.execution_manager.execution_delete(execution)
                self._reply_ok()
            elif message['command'] == 'service_inspect':
                service_id = message['service_id']
                service = config.singletons['sql_manager'].service_list(id=service_id, only_one=True)
                if service is None:
                    self._reply_error('no such service')
                else:
                    swarm = SwarmClient(config.get_conf())
                    info = swarm.inspect_container(service.docker_id)
                    self._reply_ok(info)
            else:
                log.error('Unknown command: {}'.format(message['command']))
                self._reply_error('unknown command')

            if not self.debug_has_replied:
                self._reply_error('bug')
                raise ZoeException('BUG: command {} does not fill a reply')

            config.singletons['metric'].metric_api_call(start_time, message['command'])

    def quit(self):
        self.zmq_s.close()
        self.context.term()
