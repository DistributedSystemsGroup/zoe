from sqlalchemy import Column, Integer, PickleType, ForeignKey
from sqlalchemy.orm import relationship

from zoe_scheduler.state import Base


class ApplicationState(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    description = Column(PickleType())

    executions = relationship("ExecutionState", order_by="ExecutionState.id", backref="application")

    def executions_running(self):
        ret = []
        for e in self.executions:
            if e.status == "running":
                ret.append(e)
        return ret

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description.to_dict(),
            'executions': [e.to_dict() for e in self.executions]
        }
        return ret
