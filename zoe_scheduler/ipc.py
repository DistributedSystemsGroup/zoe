import base64
from datetime import datetime
import json
import logging
import threading

from sqlalchemy.orm.exc import NoResultFound
import zmq

from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.application import ApplicationState
from zoe_scheduler.state.container import ContainerState
from zoe_scheduler.state.execution import ExecutionState
import zoe_scheduler.object_storage as storage
from zoe_scheduler.application_description import ZoeApplication
from zoe_scheduler.scheduler import ZoeScheduler
from zoe_scheduler.exceptions import InvalidApplicationDescription

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
        log.debug("IPC server thread started")
        while True:
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
    # Application descriptions
    def application_binary_get(self, application_id: int) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')
        else:
            app_data = storage.application_data_download(application)
            app_data = base64.b64encode(app_data)
            return self._reply_ok(zip_data=app_data.decode('ascii'))

    def application_binary_put(self, application_id: int, bin_data: bytes) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')
        else:
            app_data = base64.b64decode(bin_data)
            storage.application_data_upload(application, app_data)

            return self._reply_ok(zip_data=app_data.decode('ascii'))

    def application_list(self, user_id: int) -> dict:
        apps = self.state.query(ApplicationState).filter_by(user_id=user_id).all()
        return self._reply_ok(apps=[x.to_dict() for x in apps])

    def application_new(self, user_id: int, description: dict) -> dict:
        try:
            descr = ZoeApplication.from_dict(description)
        except InvalidApplicationDescription as e:
            return self._reply_error('invalid application description: %s' % e.value)

        application = ApplicationState(user_id=user_id, description=descr)
        self.state.add(application)
        self.state.commit()
        return self._reply_ok(application_id=application.id)

    def application_start(self, application_id: int) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')

        if len(application.executions) > 0:
            execution_name = str(int(sorted([x.name for x in application.executions])[-1]) + 1)
        else:
            execution_name = "1"

        execution = ExecutionState(name=execution_name,
                                   application_id=application.id,
                                   status="submitted")
        self.state.add(execution)
        self.state.flush()

        ret = self.sched.incoming(execution)
        if ret:
            execution.set_scheduled()
            self.state.commit()
            return self._reply_ok(execution_id=execution.id)
        else:
            self.state.rollback()
            return self._reply_error('admission control refused this application execution')

    def application_remove(self, application_id: int, force=False) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')
        running = self.state.query(ExecutionState).filter_by(application_id=application.id, time_finished=None).all()
        if not force and len(running) > 0:
            return self._reply_error('there are active execution, cannot delete')

        if application.description.requires_binary:
            storage.application_data_delete(application)
        for e in application.executions:
            self.execution_delete(e.id)

        self.state.delete(application)
        self.state.commit()
        return self._reply_ok()

    def application_validate(self, description: dict) -> dict:
        ret = ZoeApplication.from_dict(description)
        if ret is not None:
            return self._reply_ok()
        else:
            return self._reply_error('application description failed to validate')

    # Containers
    def container_stats(self, container_id: int) -> dict:
        ret = self.sched.platform.container_stats(container_id).to_dict()
        return self._reply_ok(**ret)

    # Executions
    def execution_delete(self, execution_id: int) -> dict:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return self._reply_error('no such execution')

        if execution.status == "running":
            self.sched.execution_terminate(self.state, execution)
            # FIXME remove it also from the scheduler, check for scheduled state

        storage.logs_archive_delete(execution)
        self.state.delete(execution)
        self.state.commit()
        return self._reply_ok()

    def execution_get(self, execution_id: int) -> dict:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return self._reply_error('no such execution')
        return self._reply_ok(**execution.to_dict())

    def execution_terminate(self, execution_id: int) -> dict:
        execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        self.sched.execution_terminate(self.state, execution)
        self.state.commit()
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
