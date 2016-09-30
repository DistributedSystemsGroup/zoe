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

"""The client side of the ZeroMQ API."""

import logging
from typing import Dict, Any, Tuple

import zmq

import zoe_lib.config as config

log = logging.getLogger(__name__)

APIReturnType = Tuple[bool, str]


class APIManager:
    """Main class for the API."""
    REQUEST_TIMEOUT = 2500  # type: int
    REQUEST_RETRIES = 1  # type: int

    def __init__(self):
        self.context = zmq.Context(1)
        self.zmq_s = None
        self.poll = zmq.Poller()
        self.master_uri = config.get_conf().master_url  # type: str
        self._connect()

    def _connect(self):
        if self.zmq_s is not None:
            return
        self.zmq_s = self.context.socket(zmq.REQ)
        self.zmq_s.connect(self.master_uri)
        self.poll.register(self.zmq_s, zmq.POLLIN)

    def _disconnect(self):
        self.zmq_s.setsockopt(zmq.LINGER, 0)
        self.zmq_s.close()
        self.poll.unregister(self.zmq_s)
        self.zmq_s = None

    def _request_reply(self, message: Dict[str, Any]) -> APIReturnType:
        """
        Implements the Lazy Pirate Pattern for a reliable client communication.
        """
        self._connect()  # Make sure we are connected
        retries_left = self.REQUEST_RETRIES
        while retries_left:
            self.zmq_s.send_json(message)  # send the message
            socks = dict(self.poll.poll(self.REQUEST_TIMEOUT))
            if socks.get(self.zmq_s) == zmq.POLLIN:  # We have a reply
                reply = self.zmq_s.recv_json()
                if reply['result'] == 'ok':
                    return True, '' if 'data' not in reply else reply['data']
                else:
                    return False, reply['message']
            else:  # Timeout
                retries_left -= 1
                log.warning('Timeout waiting for master reply')
                self._disconnect()
                if retries_left == 0:
                    log.error('Master is unreachable, abandoning API request')
                    return False, 'Master is unreachable, abandoning API request'
                log.warning('Reconnecting and retrying request...')
                self._connect()

    def execution_start(self, exec_id: int) -> APIReturnType:
        """Start an execution."""
        msg = {
            'command': 'execution_start',
            'exec_id': exec_id
        }
        return self._request_reply(msg)

    def execution_terminate(self, exec_id: int) -> APIReturnType:
        """Terminate an execution."""
        msg = {
            'command': 'execution_terminate',
            'exec_id': exec_id
        }
        return self._request_reply(msg)

    def execution_delete(self, exec_id) -> APIReturnType:
        """Delete an execution."""
        msg = {
            'command': 'execution_delete',
            'exec_id': exec_id
        }
        return self._request_reply(msg)

    def scheduler_statistics(self) -> APIReturnType:
        """Query scheduler statistics."""
        msg = {
            'command': 'scheduler_stats'
        }
        return self._request_reply(msg)
