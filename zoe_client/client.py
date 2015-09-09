import rpyc
from sqlalchemy.orm.exc import NoResultFound

from common.state import AlchemySession
from common.state.application import ApplicationState, SparkNotebookApplicationState, SparkSubmitApplicationState, SparkApplicationState, Application
from common.state.container import ContainerState
from common.state.execution import ExecutionState, SparkSubmitExecutionState, Execution
from common.state.proxy import ProxyState
from common.state.user import UserState, User
from common.application_resources import SparkApplicationResources
from common.stats import PlatformStats
from common.exceptions import UserIDDoesNotExist, ApplicationStillRunning
import common.object_storage as storage
from common.configuration import zoeconf, rpycconf

REGISTRY = zoeconf.docker_private_registry
MASTER_IMAGE = REGISTRY + "/zoerepo/spark-master"
WORKER_IMAGE = REGISTRY + "/zoerepo/spark-worker"
SUBMIT_IMAGE = REGISTRY + "/zoerepo/spark-submit"
NOTEBOOK_IMAGE = REGISTRY + "/zoerepo/spark-notebook"


class ZoeClient:
    def __init__(self, rpyc_server=None, rpyc_port=4000):
        self.rpyc_server = rpyc_server
        self.rpyc_port = rpyc_port
        self.state = AlchemySession()
        if self.rpyc_server is None:
            self.server_connection = rpyc.connect_by_service("ZoeSchedulerRPC")
        else:
            self.server_connection = rpyc.connect(self.rpyc_server, self.rpyc_port)
        self.server = self.server_connection.root

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
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 1
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkApplicationState(master_image=MASTER_IMAGE,
                                    worker_image=WORKER_IMAGE,
                                    name=name,
                                    required_resources=resources,
                                    user_id=user_id)
        self.state.add(app)
        self.state.commit()
        return app.id

    def application_spark_notebook_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> int:
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 2
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkNotebookApplicationState(master_image=MASTER_IMAGE,
                                            worker_image=WORKER_IMAGE,
                                            notebook_image=NOTEBOOK_IMAGE,
                                            name=name,
                                            required_resources=resources,
                                            user_id=user_id)
        self.state.add(app)
        self.state.commit()
        return app.id

    def application_spark_submit_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str, file_data: bytes) -> int:
        try:
            self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 2
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkSubmitApplicationState(master_image=MASTER_IMAGE,
                                          worker_image=WORKER_IMAGE,
                                          submit_image=SUBMIT_IMAGE,
                                          name=name,
                                          required_resources=resources,
                                          user_id=user_id)
        self.state.add(app)
        self.state.flush()
        storage.application_data_upload(app, file_data)

        self.state.commit()
        return app.id

    # Containers
    def container_stats(self, container_id):
        try:
            self.state.query(ContainerState).filter_by(id=container_id).one()
        except NoResultFound:
            return None
        return self.server.container_stats(container_id)

    # Executions
    def execution_delete(self, execution_id: int) -> None:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return

        if execution.status == "running":
            raise ApplicationStillRunning(execution.application)
        storage.logs_archive_delete(execution)
        self.state.delete(execution)

    def execution_get(self, execution_id: int) -> Execution:
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return None
        return execution.extract()

    def execution_get_proxy_path(self, execution_id):
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return None
        if execution is None:
            return None
        if isinstance(execution.application, SparkNotebookApplicationState):
            c = execution.find_container("spark-notebook")
            pr = self.state.query(ProxyState).filter_by(container_id=c.id, service_name="Spark Notebook interface").one()
            return zoeconf.proxy_path_url_prefix + '/{}'.format(pr.id)
        elif isinstance(execution.application, SparkSubmitApplicationState):
            c = execution.find_container("spark-submit")
            pr = self.state.query(ProxyState).filter_by(container_id=c.id, service_name="Spark application web interface").one()
            return zoeconf.proxy_path_url_prefix + '/{}'.format(pr.id)
        else:
            return None

    def execution_spark_new(self, application_id: int, name, commandline=None, spark_options=None) -> bool:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return None

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
        self.state.commit()
        ret = self.server.execution_schedule(execution.id)
        return ret

    def execution_terminate(self, execution_id: int) -> None:
        try:
            self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            pass
        self.server.execution_terminate(execution_id)

    # Logs
    def log_get(self, container_id: int) -> str:
        try:
            self.state.query(ContainerState).filter_by(id=container_id).one()
        except NoResultFound:
            return None
        else:
            ret = self.server.log_get(container_id)
            return ret

    def log_history_get(self, execution_id):
        try:
            execution = self.state.query(ExecutionState).filter_by(id=execution_id).one()
        except NoResultFound:
            return None
        return storage.logs_archive_download(execution)

    # Platform
    def platform_stats(self) -> PlatformStats:
        ret = self.server.platform_stats()
        return ret

    # Users
    def user_check(self, user_id: int) -> bool:
        user = self.state.query(UserState).filter_by(id=user_id).count()
        return user == 1

    def user_new(self, email: str) -> User:
        user = UserState(email=email)
        self.state.add(user)
        self.state.commit()
        return user.extract()

    def user_get(self, user_id: int) -> User:
        try:
            user = self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return None
        else:
            return user.extract()

    def user_get_by_email(self, email: str) -> User:
        try:
            user = self.state.query(UserState).filter_by(email=email).one()
        except NoResultFound:
            return None
        else:
            return user.extract()


def get_zoe_client() -> ZoeClient:
    if rpycconf['client_rpyc_autodiscovery']:
        return ZoeClient()
    else:
        return ZoeClient(rpycconf['client_rpyc_server'], rpycconf['client_rpyc_port'])
