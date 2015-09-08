import rpyc
from sqlalchemy.orm.exc import NoResultFound

from common.state import AlchemySession
from common.state.application import Application, SparkNotebookApplication, SparkSubmitApplication, SparkApplication, PlainApplication
from common.state.container import Container
from common.state.execution import Execution, SparkSubmitExecution, PlainExecution
from common.state.proxy import Proxy
from common.state.user import User, PlainUser
from common.application_resources import SparkApplicationResources
from common.status import PlatformStatusReport, ApplicationStatusReport
from common.exceptions import UserIDDoesNotExist, ApplicationStillRunning
import common.object_storage as storage
from common.configuration import zoeconf, rpycconf

REGISTRY = "10.1.0.1:5000"
MASTER_IMAGE = REGISTRY + "/zoe/spark-master-1.4.1:1.3"
WORKER_IMAGE = REGISTRY + "/zoe/spark-worker-1.4.1:1.3"
SHELL_IMAGE = REGISTRY + "/zoe/spark-shell-1.4.1:1.3"
SUBMIT_IMAGE = REGISTRY + "/zoe/spark-submit-1.4.1:1.3"
NOTEBOOK_IMAGE = REGISTRY + "/zoe/spark-notebook-1.4.1:1.3"


class ZoeClient:
    def __init__(self, rpyc_server=None, rpyc_port=4000):
        self.rpyc_server = rpyc_server
        self.rpyc_port = rpyc_port
        self.state = AlchemySession()
        self.server = None
        self.server_connection = None

    def _connect(self):
        if self.server is not None:
            return  # already connected
        if self.rpyc_server is None:
            self.server_connection = rpyc.connect_by_service("ZoeSchedulerRPC")
        else:
            self.server_connection = rpyc.connect(self.rpyc_server, self.rpyc_port)
        self.server = self.server_connection.root

    def _close(self):
        return

    # Users
    def user_new(self, email: str) -> PlainUser:
        user = User(email=email)
        self.state.add(user)
        self.state.commit()
        return user.extract()

    def user_get_by_email(self, email: str) -> PlainUser:
        try:
            user = self.state.query(User).filter_by(email=email).one()
        except NoResultFound:
            return None
        return user.extract()

    def user_get(self, user_id: int) -> bool:
        try:
            user = self.state.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            return None
        else:
            return user.extract()

    def user_check(self, user_id: int) -> bool:
        user = self.state.query(User).filter_by(id=user_id).count()
        return user == 1

    # Platform
    def platform_status(self) -> PlatformStatusReport:
        self._connect()
        ret = self.server.get_platform_status()
        self._close()
        return ret

    # Applications
    def spark_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> int:
        try:
            self.state.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 1
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkApplication(master_image=MASTER_IMAGE,
                               worker_image=WORKER_IMAGE,
                               name=name,
                               required_resources=resources,
                               user_id=user_id)
        self.state.add(app)
        self.state.commit()
        return app.id

    def spark_notebook_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> int:
        try:
            self.state.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 2
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkNotebookApplication(master_image=MASTER_IMAGE,
                                       worker_image=WORKER_IMAGE,
                                       notebook_image=NOTEBOOK_IMAGE,
                                       name=name,
                                       required_resources=resources,
                                       user_id=user_id)
        self.state.add(app)
        self.state.commit()
        return app.id

    def spark_submit_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str, file_data: bytes) -> int:
        try:
            self.state.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.container_count = worker_count + 2
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkSubmitApplication(master_image=MASTER_IMAGE,
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

    def application_get(self, application_id: int) -> PlainApplication:
        try:
            ret = self.state.query(Application).filter_by(id=application_id).one()
            return ret.extract()
        except NoResultFound:
            return None

    def application_get_binary(self, application_id: int) -> bytes:
        try:
            application = self.state.query(Application).filter_by(id=application_id).one()
        except NoResultFound:
            return None
        return storage.application_data_download(application)

    def application_remove(self, application_id: int):
        try:
            application = self.state.query(Application).filter_by(id=application_id).one()
        except NoResultFound:
            return
        running = self.state.query(Execution).filter_by(application_id=application.id, time_finished=None).count()
        if running > 0:
            raise ApplicationStillRunning(application)

        storage.application_data_delete(application)
        for e in application.executions:
            self.execution_delete(e.id)

        self.state.delete(application)
        self.state.commit()

    def application_status(self, application_id: int) -> ApplicationStatusReport:
        try:
            application = self.state.query(Application).filter_by(id=application_id).one()
        except NoResultFound:
            return None
        self._connect()
        ret = self.server.application_status(application.id)
        self._close()
        return ret

    def application_list(self, user_id) -> [PlainApplication]:
        try:
            self.state.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        apps = self.state.query(Application).filter_by(user_id=user_id).all()
        return [x.extract() for x in apps]

    # Executions
    def execution_spark_new(self, application_id: int, name, commandline=None, spark_options=None) -> bool:
        try:
            application = self.state.query(Application).filter_by(id=application_id).one()
        except NoResultFound:
            return None

        if type(application) is SparkSubmitApplication:
            if commandline is None:
                raise ValueError("Spark submit application requires a commandline")
            execution = SparkSubmitExecution(name=name,
                                             application_id=application.id,
                                             status="submitted",
                                             commandline=commandline,
                                             spark_opts=spark_options)
        else:
            execution = Execution(name=name,
                                  application_id=application.id,
                                  status="submitted")
        self.state.add(execution)
        self.state.commit()
        self._connect()
        ret = self.server.execution_schedule(execution.id)
        self._close()
        return ret

    def execution_get(self, execution_id: int) -> PlainExecution:
        try:
            ret = self.state.query(Execution).filter_by(id=execution_id).one()
        except NoResultFound:
            return None
        return ret.extract()

    def execution_get_proxy_path(self, execution_id):
        try:
            execution = self.state.query(Execution).filter_by(id=execution_id).one()
        except NoResultFound:
            return None
        if execution is None:
            return None
        if isinstance(execution.application, SparkNotebookApplication):
            c = execution.find_container("spark-notebook")
            pr = self.state.query(Proxy).filter_by(container_id=c.id, service_name="Spark Notebook interface").one()
            return zoeconf.proxy_path_url_prefix + '/{}'.format(pr.id)
        elif isinstance(execution.application, SparkSubmitApplication):
            c = execution.find_container("spark-submit")
            pr = self.state.query(Proxy).filter_by(container_id=c.id, service_name="Spark application web interface").one()
            return zoeconf.proxy_path_url_prefix + '/{}'.format(pr.id)
        else:
            return None

    def execution_terminate(self, execution_id: int):
        try:
            self.state.query(Execution).filter_by(id=execution_id).one()
        except NoResultFound:
            pass
        self._connect()
        self.server.execution_terminate(execution_id)
        self._close()

    def execution_delete(self, execution_id: int):
        try:
            execution = self.state.query(Execution).filter_by(id=execution_id).one()
        except NoResultFound:
            return

        if execution.status == "running":
            raise ApplicationStillRunning(execution.application)
        storage.logs_archive_delete(execution)
        self.state.delete(execution)

    # Logs
    def log_get(self, container_id: int) -> str:
        try:
            self.state.query(Container).filter_by(id=container_id).one()
        except NoResultFound:
            return None
        else:
            self._connect()
            ret = self.server.log_get(container_id)
            self._close()
            return ret

    def log_history_get(self, execution_id):
        execution = self.execution_get(execution_id)
        if execution is None:
            return None
        return storage.logs_archive_download(execution)


def get_zoe_client():
    if rpycconf['client_rpyc_autodiscovery']:
        return ZoeClient()
    else:
        return ZoeClient(rpycconf['client_rpyc_server'], rpycconf['client_rpyc_port'])
