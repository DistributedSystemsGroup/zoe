# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from contextlib import contextmanager

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


@contextmanager
def session():
    s = scoped_session(AlchemySession)
    try:
        yield s
    finally:
        s.remove()
