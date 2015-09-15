from sqlalchemy import Column, Integer, String, PickleType, ForeignKey
from sqlalchemy.orm import relationship

from zoe_scheduler.state import Base


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

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'type': self.type,
            'required_resources': self.required_resources.to_dict(),
            'executions': [e.to_dict() for e in self.executions]
        }
        return ret


class SparkApplicationState(ApplicationState):
    master_image = Column(String(256))
    worker_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-application'
    }

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret['master_image'] = self.master_image
        ret['worker_image'] = self.worker_image
        return ret


class SparkNotebookApplicationState(SparkApplicationState):
    notebook_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-notebook'
    }

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret['notebook_image'] = self.notebook_image
        return ret


class SparkSubmitApplicationState(SparkApplicationState):
    submit_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-submit'
    }

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret['submit_image'] = self.submit_image
        return ret
