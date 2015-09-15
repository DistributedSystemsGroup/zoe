from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from zoe_scheduler.state import Base


class ClusterState(Base):
    __tablename__ = 'clusters'

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('executions.id'))

    containers = relationship("ContainerState", order_by="ContainerState.id", backref="cluster")
    proxies = relationship("ProxyState", order_by="ProxyState.id", backref="cluster")
