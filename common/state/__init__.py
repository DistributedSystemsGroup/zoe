from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from common.configuration import zoeconf

Base = declarative_base()

_engine = create_engine(zoeconf.db_url, echo=False)
AlchemySession = sessionmaker(bind=_engine)

from common.state.container import Container
from common.state.cluster import Cluster
from common.state.application import Application, SparkApplication, SparkNotebookApplication, SparkSubmitApplication
from common.state.user import User
from common.state.proxy import Proxy
from common.state.execution import Execution, SparkSubmitExecution


def create_tables():
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
