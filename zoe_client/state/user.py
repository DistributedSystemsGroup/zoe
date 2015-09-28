from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from zoe_client.state import Base


class UserState(Base):
    """
    :type id: int
    :type email: str
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(128))

    applications = relationship("ApplicationState", backref="user")

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email
        }
