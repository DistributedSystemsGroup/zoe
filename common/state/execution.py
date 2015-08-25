from datetime import datetime

from sqlalchemy import Column, Integer, String, PickleType, DateTime, ForeignKey
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

    def __repr__(self):
        return "<Execution(name='%s', id='%s', assigned_resourced='%s', application_id='%s', )>" % (
            self.name, self.id, self.assigned_resources, self.application_id)


class SparkSubmitExecution(Execution):
    commandline = Column(String(1024))
    spark_opts = Column(String(1024))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-submit-application'
    }
