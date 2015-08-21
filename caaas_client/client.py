import rpyc
from sqlalchemy.orm.exc import NoResultFound

from common.state import AlchemySession, SparkApplication, User
from common.application_resources import SparkApplicationResources
from common.status import PlatformStatusReport
from common.exceptions import UserIDDoesNotExist

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
        resources.worker_resources["worker_cores"] = str(executor_cores)
        app = SparkApplication(master_image=MASTER_IMAGE, worker_image=WORKER_IMAGE, name='empty-cluster', required_resources=resources)
        self.state.add(app)
        self.state.commit()
        return app
