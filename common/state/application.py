from sqlalchemy import Column, Integer, String, PickleType, ForeignKey
from sqlalchemy.orm import relationship

from common.state import Base


class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    required_resources = Column(PickleType())  # JSON resource description
    user_id = Column(Integer, ForeignKey('users.id'))

    executions = relationship("Execution", order_by="Execution.id", backref="application")

    type = Column(String(20))  # Needed by sqlalchemy to manage class inheritance

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'application'
    }

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'name': self.name,
            'required_resources': self.required_resources.__dict__.copy(),
            'user_id': self.user_id
        }
        return ret

    def __repr__(self):
        return "<Application(name='%s', id='%s', required_resourced='%s')>" % (
            self.name, self.id, self.required_resources)

    def executions_running(self):
        ret = []
        for e in self.executions:
            if e.status == "running":
                ret.append(e)
        return ret

    def extract(self):
        ret = PlainApplication()
        ret.id = self.id
        ret.name = self.name
        ret.required_resources = self.required_resources
        ret.user_id = self.user_id
        ret.executions = [x.id for x in self.executions]
        ret.type = self.type
        return ret


class SparkApplication(Application):
    master_image = Column(String(256))
    worker_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-application'
    }

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["master_image"] = self.master_image
        ret["worker_image"] = self.worker_image
        return ret

    def extract(self):
        ret = super().extract()
        ret.master_image = self.master_image
        ret.worker_image = self.worker_image
        return ret


class SparkNotebookApplication(SparkApplication):
    notebook_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-notebook'
    }

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["notebook_image"] = self.notebook_image
        return ret

    def extract(self):
        ret = super().extract()
        ret.notebook_image = self.notebook_image
        return ret


class SparkSubmitApplication(SparkApplication):
    submit_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-submit'
    }

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["submit_image"] = self.submit_image
        return ret

    def extract(self):
        ret = super().extract()
        ret.submit_image = self.submit_image
        return ret


class PlainApplication:
    pass
