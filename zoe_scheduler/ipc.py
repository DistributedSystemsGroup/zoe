from datetime import datetime
import json
import logging
import threading

from sqlalchemy.orm.exc import NoResultFound
import zmq

from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.container import ContainerState
from zoe_scheduler.state.execution import ExecutionState
from common.application_description import ZoeApplication
from zoe_scheduler.scheduler import ZoeScheduler
from common.exceptions import InvalidApplicationDescription
from common.configuration import zoe_conf

log = logging.getLogger(__name__)


class ZoeIPCServer:
    def __init__(self, scheduler: ZoeScheduler):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://%s:%s" % (zoe_conf().ipc_listen_address, zoe_conf().ipc_listen_port))
        self.th = None
        self.state = None
        self.sched = scheduler

    def ipc_server(self, terminate: threading.Event, started: threading.Semaphore):
        log.info("IPC server started")
        started.release()
        while not terminate.wait(0):
            if self.socket.poll(timeout=1) != 0:
                message = self.socket.recv_json()
                self.state = AlchemySession()
                try:
                    reply = self._dispatch(message)
                except:
                    log.exception("Uncaught exception in IPC server thread")
                    reply = self._reply_error('exception')
                finally:
                    self.state.close()
                    self.state = None
                json_reply = json.dumps(reply, default=self._json_default_serializer)
                self.socket.send_string(json_reply)
        log.info("IPC server terminated")

    def _json_default_serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            log.error('Cannot serialize type {}'.format(type(obj)))
            raise TypeError

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
            log.error("Ignoring unknown command: {}".format(message["command"]))
            return self._reply_error('unknown command')

        return func(**message["args"])

    def _reply_ok(self, **reply) -> dict:
        return {'status': 'ok', 'answer': reply}

    def _reply_error(self, error_msg: str) -> dict:
        return {'status': 'error', 'answer': error_msg}

    # ############# Exposed methods below ################
    # Applications
    def application_validate(self, description: dict) -> dict:
        try:
            descr = ZoeApplication.from_dict(description)
        except InvalidApplicationDescription as e:
            return self._reply_error('invalid application description: %s' % e.value)
        else:
            if self.sched.validate(descr):
                return self._reply_ok()
            else:
                return self._reply_error('admission control refused this application description')

    def application_executions_get(self, application_id: int) -> dict:
        try:
            executions = self.state.query(ExecutionState).filter_by(application_id=application_id).all()
        except NoResultFound:
            return self._reply_ok(executions=[])
        else:
            return self._reply_ok(executions=[x.to_dict() for x in executions])

    # Containers
    def container_stats(self, container_id: int) -> dict:
        ret = self.sched.platform.container_stats(container_id).to_dict()
        return self._reply_ok(**ret)

    # Executions
    def _execution_kill(self, execution_id: int) -> ExecutionState:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return None

        if execution.status == "running":
            self.sched.execution_terminate(self.state, execution)
            # FIXME remove it also from the scheduler, check for scheduled state
        return execution

    def execution_delete(self, execution_id: int) -> dict:
        execution = self._execution_kill(execution_id)
        if execution is None:
            self._reply_error('no such execution')
        self.state.delete(execution)
        self.state.commit()
        return self._reply_ok()

    def execution_kill(self, execution_id: int) -> dict:
        self._execution_kill(execution_id)
        self.state.commit()
        return self._reply_ok()

    def execution_get(self, execution_id: int) -> dict:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return self._reply_error('no such execution')
        return self._reply_ok(execution=execution.to_dict())

    def execution_start(self, application_id: int, description: dict) -> dict:
        try:
            descr = ZoeApplication.from_dict(description)
        except InvalidApplicationDescription as e:
            return self._reply_error('invalid application description: %s' % e.value)

        known_executions = self.state.query(ExecutionState).filter_by(application_id=application_id).all()
        if len(known_executions) > 0:
            execution_name = str(int(sorted([x.name for x in known_executions])[-1]) + 1)
        else:
            execution_name = "1"

        execution = ExecutionState(name=execution_name,
                                   application_id=application_id,
                                   app_description=descr,
                                   status="submitted")
        self.state.add(execution)
        self.state.flush()

        self.sched.incoming(execution)
        execution.set_scheduled()
        self.state.commit()
        return self._reply_ok(execution=execution.to_dict())

    # Logs
    def log_get(self, container_id: int) -> dict:
        try:
            container = self.state.query(ContainerState).filter_by(id=container_id).one()
        except NoResultFound:
            return self._reply_error('no such container')
        else:
            ret = self.sched.platform.log_get(container)
            return self._reply_ok(log=ret)

    # Platform
    def platform_stats(self) -> dict:
        ret = self.sched.platform.status.stats()
        return self._reply_ok(**ret.to_dict())
