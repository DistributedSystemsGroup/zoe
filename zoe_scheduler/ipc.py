import logging
import threading

from sqlalchemy.orm.exc import NoResultFound
import zmq

from common.state import AlchemySession
from common.state.user import UserState

from zoe_scheduler.scheduler import ZoeScheduler

log = logging.getLogger(__name__)


class ZoeIPCServer:
    def __init__(self, scheduler: ZoeScheduler, port=8723):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:%s" % port)
        self.th = None
        self.state = AlchemySession()
        self.sched = scheduler

    def start_loop(self):
        self.th = threading.Thread(target=self._loop, name="IPC server", daemon=True)
        self.th.start()

    def _loop(self):
        log.debug("IPC server thread started")
        while True:
            message = self.socket.recv_json()
            reply = self._dispatch(message)
            self.socket.send_json(reply)

    def _dispatch(self, message: dict) -> dict:
        if "command" not in message or "args" not in message:
            log.error("Ignoring malformed message: {}".format(message))
            return self._reply_error('malformed')

        if not isinstance(message['args'], dict):
            log.error("Ignoring malformed message: {}".format(message))
            return self._reply_error('malformed')

        try:
            func = getattr(self, message["command"])
        except AttributeError:
            log.error("Ignoring unkown command: {}".format(message["command"]))
            return self._reply_error('unknown command')

        return func(**message["args"])

    def _reply_ok(self, reply: dict) -> dict:
        return {'status': 'ok', 'answer': reply}

    def _reply_error(self, error_msg: str) -> dict:
        return {'status': 'error', 'answer': error_msg}

    # Platform
    def platform_stats(self):
        ret = self.sched.platform_status.stats()
        return self._reply_ok(ret.to_dict())

    # Users
    def user_get(self, user_id) -> dict:
        try:
            user = self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return self._reply_error('no such user')
        else:
            return self._reply_ok(user.to_dict())

    def user_get_by_email(self, user_email) -> dict:
        try:
            user = self.state.query(UserState).filter_by(email=user_email).one()
        except NoResultFound:
            return self._reply_error('no such user')
        else:
            return self._reply_ok(user.to_dict())

    def user_new(self, email: str) -> dict:
        user = UserState(email=email)
        self.state.add(user)
        self.state.commit()
        return self._reply_ok(user.to_dict())
