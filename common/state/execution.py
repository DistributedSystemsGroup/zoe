from datetime import datetime

from sqlalchemy import Column, Integer, String, PickleType, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from common.state import Base


class ExecutionState(Base):
    __tablename__ = 'executions'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    assigned_resources = Column(PickleType())
    application_id = Column(Integer, ForeignKey('applications.id'))
    time_scheduled = Column(DateTime)
    time_started = Column(DateTime)
    time_finished = Column(DateTime)
    status = Column(String(32))
    termination_notice = Column(Boolean, default=False)

    cluster = relationship("ClusterState", uselist=False, backref="execution")

    type = Column(String(32))  # Needed by sqlalchemy to manage class inheritance

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'execution'
    }

    def set_scheduled(self):
        self.status = "scheduled"
        self.time_scheduled = datetime.now()

    def set_started(self):
        self.status = "running"
        self.time_started = datetime.now()

    def set_finished(self):
        self.status = "finished"
        self.time_finished = datetime.now()

    def set_terminated(self):
        self.status = "terminated"
        self.time_finished = datetime.now()

    def find_container(self, name):
        for c in self.cluster.containers:
            if c.readable_name == name:
                return c

    def extract(self):
        return Execution(self)


class SparkSubmitExecutionState(ExecutionState):
    commandline = Column(String(1024))
    spark_opts = Column(String(1024))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-submit-application'
    }

    def extract(self):
        return Execution(self)


class Execution:
    def __init__(self, execution: ExecutionState):
        self.id = execution.id
        self.name = execution.name
        self.assigned_resources = execution.assigned_resources
        self.application_id = execution.application_id
        self.time_started = execution.time_started
        self.time_scheduled = execution.time_scheduled
        self.time_finished = execution.time_finished
        self.status = execution.status
        self.termination_notice = execution.termination_notice
        if execution.cluster is not None:
            self.cluster_id = execution.cluster.id
        else:
            self.cluster_id = None
        self.type = execution.type

        if isinstance(execution, SparkSubmitExecutionState):
            self.commandline = execution.commandline
            self.spark_opts = execution.spark_opts

        self.containers = []

        if execution.cluster is not None:
            for c in execution.cluster.containers:
                self.containers.append(c.extract())
