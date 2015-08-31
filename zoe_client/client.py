import rpyc
from sqlalchemy.orm.exc import NoResultFound

from common.state import AlchemySession
from common.state.application import Application, SparkNotebookApplication, SparkSubmitApplication, SparkApplication, PlainApplication
from common.state.container import Container
from common.state.execution import Execution, SparkSubmitExecution, PlainExecution
from common.state.user import User, PlainUser
from common.application_resources import SparkApplicationResources
from common.status import PlatformStatusReport, ApplicationStatusReport
from common.exceptions import UserIDDoesNotExist, ApplicationStillRunning
import common.object_storage as storage

REGISTRY = "10.0.0.2:5000"
MASTER_IMAGE = REGISTRY + "/zoe/spark-master-1.4.1:1.2"
WORKER_IMAGE = REGISTRY + "/zoe/spark-worker-1.4.1:1.2"
SHELL_IMAGE = REGISTRY + "/zoe/spark-shell-1.4.1:1.2"
SUBMIT_IMAGE = REGISTRY + "/zoe/spark-submit-1.4.1:1.2"
NOTEBOOK_IMAGE = REGISTRY + "/zoe/spark-notebook-1.4.1:1.2"


class ZoeClient:
    def __init__(self):
        self.server_connection = rpyc.connect_by_service("ZoeSchedulerRPC")
        self.server = self.server_connection.root
        self.state = AlchemySession()

    # Users
    def user_new(self, email: str) -> PlainUser:
        user = User(email=email)
        self.state.add(user)
        self.state.commit()
        return user.extract()

    def user_get(self, email: str) -> PlainUser:
        user = self.state.query(User).filter_by(email=email).one()
        return user.extract()

    def user_check(self, user_id: int) -> bool:
        user = self.state.query(User).filter_by(id=user_id).one()
        return user is not None

    # Platform
    def platform_status(self) -> PlatformStatusReport:
        return self.server.get_platform_status()

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

    def spark_submit_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str, file: str) -> int:
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
        storage.application_data_upload(app, open(file, "rb").read())

        self.state.commit()
        return app.id

    def application_get(self, application_id) -> PlainApplication:
        try:
            ret = self.state.query(Application).filter_by(id=application_id).one()
            return ret.extract()
        except NoResultFound:
            return None

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
            self.execution_delete(e)

        self.state.delete(application)
        self.state.commit()

    def application_status(self, application_id: int) -> ApplicationStatusReport:
        try:
            application = self.state.query(Application).filter_by(id=application_id).one()
        except NoResultFound:
            return None
        return self.server.application_status(application.id)

    def spark_application_list(self, user_id) -> [PlainApplication]:
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
        return self.server.execution_schedule(execution.id)

    def execution_get(self, execution_id: int) -> PlainExecution:
        try:
            ret = self.state.query(Execution).filter_by(id=execution_id).one()
        except NoResultFound:
            return None
        return ret.extract()

    def execution_terminate(self, execution_id: int):
        try:
            self.state.query(Execution).filter_by(id=execution_id).one()
        except NoResultFound:
            pass
        self.server.terminate_execution(execution_id)

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
            return self.server.log_get(container_id)
