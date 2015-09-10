import base64
import logging

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.ipc import ZoeIPCClient
from common.state import AlchemySession
from common.state.application import ApplicationState, Application
from common.state.execution import ExecutionState
from common.state.user import UserState
from common.exceptions import UserIDDoesNotExist, ApplicationStillRunning
import common.object_storage as storage
from common.configuration import zoeconf
from zoe_client.entities import User, Execution

log = logging.getLogger(__name__)

REGISTRY = zoeconf.docker_private_registry
MASTER_IMAGE = REGISTRY + "/zoerepo/spark-master"
WORKER_IMAGE = REGISTRY + "/zoerepo/spark-worker"
SUBMIT_IMAGE = REGISTRY + "/zoerepo/spark-submit"
NOTEBOOK_IMAGE = REGISTRY + "/zoerepo/spark-notebook"


class ZoeClient:
    def __init__(self, ipc_server='localhost', ipc_port=8723):
        self.ipc_server = ZoeIPCClient(ipc_server, ipc_port)
        self.state = AlchemySession()

    # Applications
    def application_get(self, application_id: int) -> Application:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return None
        return application.extract()

    def application_get_binary(self, application_id: int) -> bytes:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return None
        return storage.application_data_download(application)

    def application_list(self, user_id):
        """
        Returns a list of all Applications belonging to user_id
        :type user_id: int
        :rtype : list[Application]
        """
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        apps = self.state.query(ApplicationState).filter_by(user_id=user_id).all()
        return [x.extract() for x in apps]

    def application_remove(self, application_id: int):
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return
        running = self.state.query(ExecutionState).filter_by(application_id=application.id, time_finished=None).count()
        if running > 0:
            raise ApplicationStillRunning(application)

        storage.application_data_delete(application)
        for e in application.executions:
            self.execution_delete(e.id)

        self.state.delete(application)
        self.state.commit()

    def application_spark_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> int:
        answer = self.ipc_server.ask('application_spark_new',
                                     user_id=user_id,
                                     worker_count=worker_count,
                                     executor_memory=executor_memory,
                                     executor_cores=executor_cores,
                                     name=name,
                                     master_image=MASTER_IMAGE,
                                     worker_image=WORKER_IMAGE)
        if answer is not None:
            return answer['app_id']

    def application_spark_notebook_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> int:
        answer = self.ipc_server.ask('application_spark_notebook_new',
                                     user_id=user_id,
                                     worker_count=worker_count,
                                     executor_memory=executor_memory,
                                     executor_cores=executor_cores,
                                     name=name,
                                     master_image=MASTER_IMAGE,
                                     worker_image=WORKER_IMAGE,
                                     notebook_image=NOTEBOOK_IMAGE)
        if answer is not None:
            return answer['app_id']

    def application_spark_submit_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str, file_data: bytes) -> int:
        file_data = base64.b64encode(file_data).decode('ascii')
        answer = self.ipc_server.ask('application_spark_submit_new',
                                     user_id=user_id,
                                     worker_count=worker_count,
                                     executor_memory=executor_memory,
                                     executor_cores=executor_cores,
                                     name=name,
                                     file_data=file_data,
                                     master_image=MASTER_IMAGE,
                                     worker_image=WORKER_IMAGE,
                                     submit_image=SUBMIT_IMAGE)
        if answer is not None:
            return answer['app_id']

    # Containers
    def container_stats(self, container_id):
        return self.ipc_server.ask('container_stats', container_id=container_id)

    # Executions
    def execution_delete(self, execution_id: int) -> None:
        ret = self.ipc_server.ask('execution_delete', execution_id=execution_id)
        return ret is not None

    def execution_get(self, execution_id: int) -> Execution:
        exec_dict = self.ipc_server.ask('execution_get', execution_id=execution_id)
        if exec_dict is not None:
            return Execution(exec_dict)

    def execution_get_proxy_path(self, execution_id):
        answer = self.ipc_server.ask('execution_get_proxy_path', execution_id=execution_id)
        if answer is not None:
            return answer['path']

    def execution_spark_new(self, application_id: int, name, commandline=None, spark_options=None) -> bool:
        ret = self.ipc_server.ask('execution_spark_new', application_id=application_id, name=name, commandline=commandline, spark_options=spark_options)
        return ret is not None

    def execution_terminate(self, execution_id: int) -> None:
        ret = self.ipc_server.ask('execution_terminate', execution_id=execution_id)
        return ret is not None

    # Logs
    def log_get(self, container_id: int) -> str:
        clog = self.ipc_server.ask('log_get', container_id=container_id)
        if clog is not None:
            return clog['log']

    def log_history_get(self, execution_id):
        data = self.ipc_server.ask('log_history_get', execution_id=execution_id)
        log_data = base64.b64decode(data['zip_data'])
        return log_data

    # Platform
    def platform_stats(self) -> dict:
        stats = self.ipc_server.ask('platform_stats')
        return stats

    # Users
    def user_check(self, user_id: int) -> bool:
        user = self.user_get(user_id)
        return user is not None

    def user_new(self, email: str) -> User:
        user_dict = self.ipc_server.ask('user_new', email=email)
        if user_dict is not None:
            return User(user_dict)

    def user_get(self, user_id: int) -> User:
        user_dict = self.ipc_server.ask('user_get', user_id=user_id)
        if user_dict is not None:
            return User(user_dict)

    def user_get_by_email(self, email: str) -> User:
        user_dict = self.ipc_server.ask('user_get_by_email', user_email=email)
        if user_dict is not None:
            return User(user_dict)
