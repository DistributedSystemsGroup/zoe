from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from common.state import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(128))

    applications = relationship("Application", order_by="Application.id", backref="user")

    def __repr__(self):
        return "<User(id='%s', email='%s')>" % (
            self.id, self.app_id)

    def extract(self):
        ret = PlainUser()
        ret.id = self.id
        ret.email = self.email
        return ret


class PlainUser:
    id = None
    email = None

