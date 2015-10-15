# Copyright (c) 2015, Daniele Venzano
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

"""
This module contains the implementation of the client side of the internal Zoe IPC protocol.
The protocol is based on ZeroMQ, used to exchange JSON messages.

Clients should never have to use this module directly.
"""

import logging

import zmq

from common.configuration import zoe_conf

log = logging.getLogger(__name__)


class ZoeIPCClient:
    """
    This class implements the Zoe IPC client.
    """
    def __init__(self, server=None, port=None):
        """
        Initialize the ZMQ library and connect to the IPC server.

        :param server: IP address or hostname of the server
        :param port: port of the IPC server
        """
        if server is None:
            server = zoe_conf().ipc_server
        if port is None:
            port = zoe_conf().ipc_port

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.RCVTIMEO = 2000
        self.socket.connect("tcp://%s:%d" % (server, port))
#        log.debug("ZMQ socket connected")

    def _ask(self, message: dict) -> dict:
        """
        Send the IPC message, manage the various exceptions and eventually return the answer.

        :param message: the message to send
        :return: an answer or None
        """
        self.socket.send_json(message)
        try:
            answer = self.socket.recv_json()
        except zmq.error.Again:
            log.error("ZMQ is asking to try again, we drop the message")
            return None
        except zmq.ZMQError as e:
            log.error("IPC server error: {}".format(e.msg))
            return None
        if self._is_error(answer):
            log.info("IPC error: {}".format(self._error(answer)))
            return None
        else:
            return self._answer(answer)

    def ask(self, command: str, **kwargs) -> dict:
        """
        Ask the IPC server to execute the given command.

        :param command: the command to execute
        :param kwargs: command arguments that will be passed along in the message
        :return: an answer, or None
        """
        q = {
            'command': command,
            'args': kwargs
        }
        return self._ask(q)

    def _is_error(self, message: dict) -> bool:
        """
        Check if the answer is an error.

        :param message: answer to check
        :return: True if message contains an error, False otherwise
        """
        return message['status'] == 'error'

    def _error(self, message: dict) -> str:
        """
        Extract the error string from an answer, this method should be called only if _is_error(message) is True.

        :param message: answer
        :return: the error string
        """
        return message['answer']

    def _answer(self, message: dict) -> dict:
        """
        Extract the real content from the IPC answer, this method should be called only if _is_error(message) is True.

        :param message:
        :return:
        """
        return message['answer']
