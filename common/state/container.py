from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from common.state import Base


class ContainerState(Base):
    __tablename__ = 'containers'

    id = Column(Integer, primary_key=True)
    docker_id = Column(String(128))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    ip_address = Column(String(16))
    readable_name = Column(String(32))

    proxies = relationship("ProxyState", order_by="ProxyState.id", backref="container")

    def extract(self):
        """
        Generates a normal object not attached to SQLAlchemy
        :rtype : Container
        """
        return Container(self)


class Container:
    def __init__(self, container: ContainerState):
        self.id = container.id
        self.docker_id = container.docker_id
        self.cluster_id = container.cluster_id
        self.ip_address = container.ip_address
        self.readable_name = container.readable_name

        self.proxies = []

        for p in container.proxies:
            self.proxies.append(p.extract())
