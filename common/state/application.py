import json

from sqlalchemy import Column, Integer, String, PickleType, Text, ForeignKey

from common.state import Base


class TextPickleType(PickleType):
    impl = Text


class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    required_resources = Column(TextPickleType(pickler=json))  # JSON resource description
    user_id = Column(Integer, ForeignKey('users.id'))

    type = Column(String(20))  # Needed by sqlalchemy to manage class inheritance

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'application'
    }

    def __repr__(self):
        return "<Application(name='%s', id='%s', required_resourced='%s')>" % (
            self.name, self.id, self.required_resources)


class SparkApplication(Application):
    master_image = Column(String(256))
    worker_image = Column(String(256))

    __mapper_args__ = {
        'polymorphic_identity': 'spark-application'
    }
