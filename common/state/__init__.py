from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from common.configuration import conf

Base = declarative_base()

_engine = create_engine(conf["db_connection"], echo=False)
AlchemySession = sessionmaker(bind=_engine)

from common.state.container import Container
from common.state.cluster import Cluster
from common.state.application import Application, SparkApplication
from common.state.user import User


def create_tables():
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
