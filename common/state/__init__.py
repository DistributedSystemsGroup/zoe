from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from common.configuration import zoeconf

Base = declarative_base()

_engine = create_engine(zoeconf.db_url, echo=False)
AlchemySession = sessionmaker(bind=_engine)

from common.state.container import ContainerState
from common.state.cluster import ClusterState
from common.state.application import ApplicationState, SparkApplicationState, SparkNotebookApplicationState, SparkSubmitApplicationState
from common.state.user import UserState
from common.state.proxy import ProxyState
from common.state.execution import ExecutionState, SparkSubmitExecutionState


def create_tables():
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
