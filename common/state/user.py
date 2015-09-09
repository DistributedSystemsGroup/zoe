from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from common.state import Base


class UserState(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(128))

    applications = relationship("ApplicationState", order_by="ApplicationState.id", backref="user")

    def extract(self):
        return User(self)


class User:
    def __init__(self, user: UserState):
        self.id = user.id
        self.email = user.email
