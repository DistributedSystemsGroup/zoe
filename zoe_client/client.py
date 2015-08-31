import rpyc
from sqlalchemy.orm.exc import NoResultFound

from common.state import AlchemySession, SparkApplication, User, Application, Cluster, SparkSubmitExecution, Execution, SparkNotebookApplication, SparkSubmitApplication
from common.application_resources import SparkApplicationResources
from common.status import PlatformStatusReport
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

    def user_new(self, email) -> int:
        user = User(email=email)
        self.state.add(user)
        self.state.commit()
        return user.id

    def user_get(self, email) -> int:
        user = self.state.query(User).filter_by(email=email).one()
        return user.id

    def platform_status(self) -> PlatformStatusReport:
        return self.server.get_platform_status()

    def spark_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str) -> SparkApplication:
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
        return app

    def spark_notebook_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str):
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
        return app

    def spark_submit_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int, name: str, file: str) -> SparkSubmitApplication:
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
        return app

    def spark_application_get(self, application_id) -> Application:
        try:
            return self.state.query(SparkApplication).filter_by(id=application_id).one()
        except NoResultFound:
            return None

    def execution_spark_new(self, application: Application, name, commandline=None, spark_options=None):
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

    def application_remove(self, application: Application):
        running = self.state.query(Execution).filter_by(application_id=application.id, time_finished=None).count()
        if running > 0:
            raise ApplicationStillRunning(application)
        self.state.delete(application)
        self.state.commit()

    def application_status(self, application: Application):
        return self.server.application_status(application.id)

    def spark_application_list(self, user_id):
        try:
            self.state.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        return self.state.query(Application).filter_by(user_id=user_id).all()

    def execution_get(self, execution_id: int) -> Execution:
        return self.state.query(Execution).filter_by(id=execution_id).one()

    def execution_terminate(self, execution: Execution):
        self.server.terminate_execution(execution.id)

    def log_get(self, container_id: int) -> str:
        return self.server.log_get(container_id)
