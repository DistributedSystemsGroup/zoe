import logging

import zmq

from common.configuration import zoe_conf

log = logging.getLogger(__name__)


class ZoeIPCClient:
    def __init__(self, server=None, port=None):
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
        q = {
            'command': command,
            'args': kwargs
        }
        return self._ask(q)

    def _is_error(self, message: dict) -> bool:
        return message['status'] == 'error'

    def _error(self, message: dict) -> str:
        return message['answer']

    def _answer(self, message: dict) -> dict:
        return message['answer']
