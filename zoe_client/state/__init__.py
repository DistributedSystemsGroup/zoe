from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
AlchemySession = sessionmaker()

from zoe_client.state.user import UserState


def init(db_url):
    global AlchemySession
    engine = create_engine(db_url, echo=False)
    AlchemySession.configure(bind=engine)
    return engine


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def session():
    return scoped_session(AlchemySession)
