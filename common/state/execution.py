from datetime import datetime

from sqlalchemy import Column, Integer, String, PickleType, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from common.state import Base


class Execution(Base):
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

    cluster = relationship("Cluster", uselist=False, backref="execution")

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

    def __repr__(self):
        return "<Execution(name='%s', id='%s', assigned_resourced='%s', application_id='%s', )>" % (
            self.name, self.id, self.assigned_resources, self.application_id)

    def extract(self):
        ret = PlainExecution()
        ret.id = self.id
        ret.name = self.name
        ret.assigned_resources = self.assigned_resources
        ret.application_id = self.application_id
        ret.time_started = self.time_started
        ret.time_scheduled = self.time_scheduled
        ret.time_finished = self.time_finished
        ret.status = self.status
        ret.termination_notice = self.termination_notice
        if self.cluster is not None:
            ret.cluster_id = self.cluster.id
        ret.type = self.type
        return ret


class SparkSubmitExecution(Execution):
    commandline = Column(String(1024))
    spark_opts = Column(String(1024))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-submit-application'
    }

    def extract(self):
        ret = super().extract()
        ret.commandline = self.commandline
        ret.spark_opts = self.spark_opts
        return ret


class PlainExecution:
    id = None
    name = None
    assigned_resources = None
    application_id = None
    time_started = None
    time_scheduled = None
    time_finished = None
    status = None
    termination_notice = None
    cluster_id = None
    type = None
    commandline = None
    spark_opts = None
