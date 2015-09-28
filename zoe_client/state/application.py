from sqlalchemy import Column, Integer, PickleType, ForeignKey

from zoe_client.state import Base

from common.application_description import ZoeApplication


class ApplicationState(Base):
    """
    :type id: int
    :type user_id: int
    :type description: ZoeApplication
    """
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(PickleType())

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description.to_dict(),
        }
        return ret
