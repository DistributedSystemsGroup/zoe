from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
AlchemySession = sessionmaker()

_engine = None


def init(db_url):
    global _engine, AlchemySession
    if _engine is None:
        _engine = create_engine(db_url, echo=False)
        AlchemySession.configure(bind=_engine)


def create_tables():
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
