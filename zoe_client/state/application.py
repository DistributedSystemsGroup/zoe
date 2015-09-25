from sqlalchemy import Column, Integer, PickleType, ForeignKey

from zoe_client.state import Base


class ApplicationState(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(PickleType())

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description.copy(),
        }
        return ret
