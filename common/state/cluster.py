from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from common.state import Base


class Cluster(Base):
    __tablename__ = 'clusters'

    id = Column(Integer, primary_key=True)
    app_id = Column(Integer)

    containers = relationship("Container", order_by="Container.id", backref="cluster")

    def __repr__(self):
        return "<Cluster(id='%s', app_id='%s')>" % (
            self.id, self.app_id)
