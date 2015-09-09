from sqlalchemy import Column, Integer, String, PickleType, ForeignKey
from sqlalchemy.orm import relationship

from common.state import Base


class ApplicationState(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    required_resources = Column(PickleType())  # JSON resource description
    user_id = Column(Integer, ForeignKey('users.id'))

    executions = relationship("ExecutionState", order_by="ExecutionState.id", backref="application")

    type = Column(String(20))  # Needed by sqlalchemy to manage class inheritance

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'application'
    }

    def executions_running(self):
        ret = []
        for e in self.executions:
            if e.status == "running":
                ret.append(e)
        return ret

    def extract(self):
        return Application(self)


class SparkApplicationState(ApplicationState):
    master_image = Column(String(256))
    worker_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-application'
    }

    def extract(self):
        return Application(self)


class SparkNotebookApplicationState(SparkApplicationState):
    notebook_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-notebook'
    }

    def extract(self):
        return Application(self)


class SparkSubmitApplicationState(SparkApplicationState):
    submit_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-submit'
    }

    def extract(self):
        return Application(self)


class Application:
    """
    :type id: int
    :type name: str
    :type required_resources: ApplicationResources
    :type user_id: int
    :type type: str
    :type master_image: str
    :type worker_image: str
    :type notebook_image: str
    :type submit_image: str
    :type executions: list[Execution]
    """
    def __init__(self, application: ApplicationState) -> None:
        self.id = application.id
        self.name = application.name
        self.required_resources = application.required_resources
        self.user_id = application.user_id
        self.type = application.type
        if isinstance(application, SparkApplicationState):
            self.master_image = application.master_image
            self.worker_image = application.worker_image
        if isinstance(application, SparkNotebookApplicationState):
            self.notebook_image = application.notebook_image
        if isinstance(application, SparkSubmitApplicationState):
            self.submit_image = application.submit_image

        self.executions = []

        for e in application.executions:
            self.executions.append(e.extract())

    def __str__(self):
        s = "Application"
        s += " - Name: {}".format(self.name)
        s += " - Type: {}".format(self.type)
        # FIXME add missing fields
        return s
