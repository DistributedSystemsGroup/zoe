from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from common.state import Base


class Cluster(Base):
    __tablename__ = 'clusters'

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('executions.id'))

    containers = relationship("Container", order_by="Container.id", backref="cluster")
    proxies = relationship("Proxy", order_by="Proxy.id", backref="cluster")

    def __repr__(self):
        return "<Cluster(id='%s', execution_id='%s')>" % (
            self.id, self.execution_id)
