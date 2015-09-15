from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from zoe_scheduler.state import Base


class ContainerState(Base):
    __tablename__ = 'containers'

    id = Column(Integer, primary_key=True)
    docker_id = Column(String(128))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    ip_address = Column(String(16))
    readable_name = Column(String(32))

    proxies = relationship("ProxyState", order_by="ProxyState.id", backref="container")

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'docker_id': self.docker_id,
            'cluster_id': self.cluster_id,
            'ip_address': self.ip_address,
            'readable_name': self.readable_name,
            'proxies': []
        }

        for p in self.proxies:
            ret['proxies'].append(p.to_dict())

        return ret
