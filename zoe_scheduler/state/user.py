from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from zoe_scheduler.state import Base


class UserState(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(128))

    applications = relationship("ApplicationState", order_by="ApplicationState.id", backref="user")

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email
        }
