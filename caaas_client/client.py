import rpyc
from sqlalchemy.orm.exc import NoResultFound

from common.state import AlchemySession, SparkApplication, User, Application, Cluster, SparkSubmitExecution, Execution
from common.application_resources import SparkApplicationResources
from common.status import PlatformStatusReport
from common.exceptions import UserIDDoesNotExist, ApplicationStillRunning

REGISTRY = "10.0.0.2:5000"
MASTER_IMAGE = REGISTRY + "/venza/spark-master:1.4.1"
WORKER_IMAGE = REGISTRY + "/venza/spark-worker:1.4.1"
SHELL_IMAGE = REGISTRY + "/venza/spark-shell:1.4.1"
SUBMIT_IMAGE = REGISTRY + "/venza/spark-submit:1.4.1"
NOTEBOOK_IMAGE = REGISTRY + "/venza/spark-notebook:1.4.1"


class CAaaSClient:
    def __init__(self):
        self.server_connection = rpyc.connect_by_service("CAaaSSchedulerRPC")
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

    def spark_application_new(self, user_id: int, worker_count: int, executor_memory: str, executor_cores: int) -> SparkApplication:
        try:
            user = self.state.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            raise UserIDDoesNotExist(user_id)

        resources = SparkApplicationResources()
        resources.worker_count = worker_count
        resources.worker_resources["memory_limit"] = executor_memory
        resources.worker_resources["cores"] = executor_cores
        app = SparkApplication(master_image=MASTER_IMAGE, worker_image=WORKER_IMAGE, name='empty-cluster', required_resources=resources, user_id=user_id)
        self.state.add(app)
        self.state.commit()
        return app

    def spark_application_get(self, application_id):
        try:
            return self.state.query(SparkApplication).filter_by(id=application_id).one()
        except NoResultFound:
            return None

    def execution_spark_submit_new(self, application: Application, name, commandline, spark_options):
        execution = SparkSubmitExecution(name=name,
                                         application_id=application.id,
                                         status="submitted",
                                         commandline=commandline,
                                         spark_opts=spark_options)
        self.state.add(execution)
        self.state.commit()
        return self.server.execution_schedule(execution.id)

    def execution_spark_cluster_new(self, application: Application, name):
        execution = Execution(name=name,
                              application_id=application.id,
                              status="submitted")
        self.state.add(execution)
        self.state.commit()
        return self.server.execution_schedule(execution.id)

    def application_remove(self, application: Application):
        running = self.state.query(Cluster).filter_by(app_id=application.id).count()
        if running > 0:
            raise ApplicationStillRunning(application)
        self.state.delete(application)
        self.state.commit()

    def application_status(self, application: Application):
        return self.server.application_status(application.id)

    def execution_get(self, execution_id: int) -> Execution:
        return self.state.query(Execution).filter_by(id=execution_id).one()

    def execution_terminate(self, execution: Execution):
        self.server.terminate_execution(execution.id)
