from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
AlchemySession = sessionmaker()

from zoe_scheduler.state.application import ApplicationState, SparkSubmitApplicationState, SparkApplicationState, SparkNotebookApplicationState
from zoe_scheduler.state.cluster import ClusterState
from zoe_scheduler.state.container import ContainerState
from zoe_scheduler.state.execution import ExecutionState, SparkSubmitExecutionState
from zoe_scheduler.state.proxy import ProxyState
from zoe_scheduler.state.user import UserState


def init(db_url):
    global AlchemySession
    engine = create_engine(db_url, echo=False)
    AlchemySession.configure(bind=engine)
    return engine


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
