import base64
from datetime import datetime
import json
import logging
import threading

from sqlalchemy.orm.exc import NoResultFound
import zmq

from common.application_resources import SparkApplicationResources
from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.application import ApplicationState, SparkSubmitApplicationState, SparkNotebookApplicationState, SparkApplicationState
from zoe_scheduler.state.container import ContainerState
from zoe_scheduler.state.execution import ExecutionState, SparkSubmitExecutionState
from zoe_scheduler.state.proxy import ProxyState
from zoe_scheduler.state.user import UserState
import zoe_scheduler.object_storage as storage
from common.configuration import zoeconf
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
            log.error("Ignoring unkown command: {}".format(message["command"]))
            return self._reply_error('unknown command')

        return func(**message["args"])

    def _reply_ok(self, **reply) -> dict:
        return {'status': 'ok', 'answer': reply}

    def _reply_error(self, error_msg: str) -> dict:
        return {'status': 'error', 'answer': error_msg}

    # ############# Exposed methods below ################
    # Applications
    def application_get(self, application_id: int) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')
        return self._reply_ok(app=application.to_dict())

    def application_get_binary(self, application_id: int) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')
        else:
            app_data = storage.application_data_download(application)
            app_data = base64.b64encode(app_data)
            return self._reply_ok(zip_data=app_data.decode('ascii'))

    def application_list(self, user_id: int) -> dict:
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return self._reply_error('no such user')

        apps = self.state.query(ApplicationState).filter_by(user_id=user_id).all()
        return self._reply_ok(apps=[x.to_dict() for x in apps])

    def application_remove(self, application_id: int, force=False) -> dict:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return self._reply_error('no such application')
        running = self.state.query(ExecutionState).filter_by(application_id=application.id, time_finished=None).all()
        if not force and len(running) > 0:
            return self._reply_error('there are active execution, cannot delete')

        storage.application_data_delete(application)
        for e in application.executions:
            self.execution_delete(e.id)

        self.state.delete(application)
        self.state.commit()
        return self._reply_ok()

    def application_spark_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str,
                              master_image: str, worker_image: str) -> dict:
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return self._reply_error('no such user')

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 1
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkApplicationState(master_image=master_image,
                                    worker_image=worker_image,
                                    name=name,
                                    required_resources=resources,
                                    user_id=user_id)
        self.state.add(app)
        self.state.commit()
        return self._reply_ok(app_id=app.id)

    def application_spark_notebook_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str,
                                       master_image: str, worker_image: str, notebook_image: str) -> dict:
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return self._reply_error('no such user')

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 2
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkNotebookApplicationState(master_image=master_image,
                                            worker_image=worker_image,
                                            notebook_image=notebook_image,
                                            name=name,
                                            required_resources=resources,
                                            user_id=user_id)
        self.state.add(app)
        self.state.commit()
        return self._reply_ok(app_id=app.id)

    def application_spark_submit_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str, file_data: bytes,
                                     master_image: str, worker_image: str, submit_image: str) -> dict:
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return self._reply_error('no such user')

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 2
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkSubmitApplicationState(master_image=master_image,
                                          worker_image=worker_image,
                                          submit_image=submit_image,
                                          name=name,
                                          required_resources=resources,
                                          user_id=user_id)
        self.state.add(app)
        self.state.flush()
        storage.application_data_upload(app, file_data)

        self.state.commit()
        return self._reply_ok(app_id=app.id)

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

    def execution_get_proxy_path(self, execution_id: int) -> dict:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return self._reply_error('no such execution')

        if isinstance(execution.application, SparkNotebookApplicationState):
            c = execution.find_container("spark-notebook")
            pr = self.state.query(ProxyState).filter_by(container_id=c.id, service_name="Spark Notebook interface").one()
            path = zoeconf().proxy_path_url_prefix + '/{}'.format(pr.id)
            return self._reply_ok(path=path)
        elif isinstance(execution.application, SparkSubmitApplicationState):
            c = execution.find_container("spark-submit")
            pr = self.state.query(ProxyState).filter_by(container_id=c.id, service_name="Spark application web interface").one()
            path = zoeconf().proxy_path_url_prefix + '/{}'.format(pr.id)
            return self._reply_ok(path=path)
        else:
            return self._reply_error('unknown application type')

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
        self.state.flush()

        ret = self.sched.incoming(execution)
        if ret:
            execution.set_scheduled()
            self.state.commit()
        else:
            self._reply_error('admission control refused this application execution')
            self.state.rollback()

        return self._reply_ok(execution_id=execution.id)

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
