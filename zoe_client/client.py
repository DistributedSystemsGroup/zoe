import base64
import logging

from zoe_client.ipc import ZoeIPCClient
from common.configuration import zoeconf
from zoe_client.entities import User, Execution, Application

log = logging.getLogger(__name__)

MASTER_IMAGE = "/zoerepo/spark-master"
WORKER_IMAGE = "/zoerepo/spark-worker"
SUBMIT_IMAGE = "/zoerepo/spark-submit"
NOTEBOOK_IMAGE = "/zoerepo/spark-notebook"


class ZoeClient:
    def __init__(self, ipc_server='localhost', ipc_port=8723):
        self.ipc_server = ZoeIPCClient(ipc_server, ipc_port)
        self.image_registry = zoeconf().docker_private_registry

    # Applications
    def application_get(self, application_id: int) -> Application:
        answer = self.ipc_server.ask('application_get', application_id=application_id)
        if answer is not None:
            return Application(answer['app'])

    def application_get_binary(self, application_id: int) -> bytes:
        data = self.ipc_server.ask('application_get_binary', application_id=application_id)
        app_data = base64.b64decode(data['zip_data'])
        return app_data

    def application_list(self, user_id):
        """
        Returns a list of all Applications belonging to user_id
        :type user_id: int
        :rtype : list[Application]
        """
        answer = self.ipc_server.ask('application_list', user_id=user_id)
        if answer is None:
            return []
        else:
            return [Application(x) for x in answer['apps']]

    def application_remove(self, application_id: int, force: bool) -> bool:
        answer = self.ipc_server.ask('application_remove', application_id=application_id, force=force)
        return answer is not None

    def application_spark_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> int:
        answer = self.ipc_server.ask('application_spark_new',
                                     user_id=user_id,
                                     worker_count=worker_count,
                                     executor_memory=executor_memory,
                                     executor_cores=executor_cores,
                                     name=name,
                                     master_image=self.image_registry + MASTER_IMAGE,
                                     worker_image=self.image_registry + WORKER_IMAGE)
        if answer is not None:
            return answer['app_id']

    def application_spark_notebook_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> int:
        answer = self.ipc_server.ask('application_spark_notebook_new',
                                     user_id=user_id,
                                     worker_count=worker_count,
                                     executor_memory=executor_memory,
                                     executor_cores=executor_cores,
                                     name=name,
                                     master_image=self.image_registry + MASTER_IMAGE,
                                     worker_image=self.image_registry + WORKER_IMAGE,
                                     notebook_image=self.image_registry + NOTEBOOK_IMAGE)
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
                                     master_image=self.image_registry + MASTER_IMAGE,
                                     worker_image=self.image_registry + WORKER_IMAGE,
                                     submit_image=self.image_registry + SUBMIT_IMAGE)
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
