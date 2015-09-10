import base64
import logging
import threading

from sqlalchemy.orm.exc import NoResultFound
import zmq

from common.state import AlchemySession
from common.state.application import ApplicationState, SparkSubmitApplicationState
from common.state.container import ContainerState
from common.state.execution import ExecutionState, SparkSubmitExecutionState
from common.state.user import UserState
import common.object_storage as storage

from zoe_scheduler.scheduler import ZoeScheduler

log = logging.getLogger(__name__)


class ZoeIPCServer:
    def __init__(self, scheduler: ZoeScheduler, port=8723):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:%s" % port)
        self.th = None
        self.state = None
        self.sched = scheduler

    def start_thread(self):
        self.th = threading.Thread(target=self._loop, name="IPC server", daemon=True)
        self.th.start()

    def _loop(self):
        self.state = AlchemySession()  # thread-local session
        log.debug("IPC server thread started")
        while True:
            message = self.socket.recv_json()
            try:
                reply = self._dispatch(message)
            except:
                log.exception("Uncaught exception in IPC server thread")
                reply = self._reply_error('exception')
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

    def _reply_ok(self, **reply) -> dict:
        return {'status': 'ok', 'answer': reply}

    def _reply_error(self, error_msg: str) -> dict:
        return {'status': 'error', 'answer': error_msg}

    # ############# Exposed methods below ################
    # Containers
    def container_stats(self, container_id: int) -> dict:
        ret = self.sched.platform.container_stats(container_id).to_dict()
        return self._reply_ok(**ret)

    # Executions
    def execution_spark_new(self, application_id: int, name: str, commandline=None, spark_options=None) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')

        if type(application) is SparkSubmitApplicationState:
            if commandline is None:
                raise ValueError("Spark submit application requires a commandline")
            execution = SparkSubmitExecutionState(name=name,
                                                  application_id=application.id,
                                                  status="submitted",
                                                  commandline=commandline,
                                                  spark_opts=spark_options)
        else:
            execution = ExecutionState(name=name,
                                       application_id=application.id,
                                       status="submitted")
        self.state.add(execution)

        ret = self.sched.incoming(execution)
        if ret:
            execution.set_scheduled()
            self.state.commit()
        else:
            self._reply_error('admission control refused this application execution')
            self.state.rollback()

        return self._reply_ok()

    def execution_terminate(self, execution_id: int) -> dict:
        state = AlchemySession()
        execution = state.query(ExecutionState).filter_by(id=execution_id).one()
        self.sched.execution_terminate(state, execution)
        state.commit()
        state.close()
        return self._reply_ok()

    # Logs
    def log_get(self, container_id: int) -> dict:
        try:
            container = self.state.query(ContainerState).filter_by(id=container_id).one()
        except NoResultFound:
            return self._reply_error('no such container')
        else:
            ret = self.sched.platform.log_get(container)
            return self._reply_ok(log=ret)

    def log_history_get(self, execution_id) -> dict:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return self._reply_error('no such execution')
        log_data = storage.logs_archive_download(execution)
        log_data = base64.b64encode(log_data)
        return self._reply_ok(zip_data=log_data.decode('ascii'))

    # Platform
    def platform_stats(self) -> dict:
        ret = self.sched.platform_status.stats()
        return self._reply_ok(**ret.to_dict())

    # Users
    def user_get(self, user_id) -> dict:
        try:
            user = self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return self._reply_error('no such user')
        else:
            return self._reply_ok(**user.to_dict())

    def user_get_by_email(self, user_email) -> dict:
        try:
            user = self.state.query(UserState).filter_by(email=user_email).one()
        except NoResultFound:
            return self._reply_error('no such user')
        else:
            return self._reply_ok(**user.to_dict())

    def user_new(self, email: str) -> dict:
        user = UserState(email=email)
        self.state.add(user)
        self.state.commit()
        return self._reply_ok(**user.to_dict())
