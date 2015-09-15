from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func

from zoe_scheduler.state import Base


class ProxyState(Base):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)
    internal_url = Column(String(1024))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    container_id = Column(Integer, ForeignKey('containers.id'))
    service_name = Column(String(32))
    last_access = Column(DateTime, default=func.now())

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'internal_url': self.internal_url,
            'cluster_id': self.cluster_id,
            'container_id': self.container_id,
            'service_name': self.service_name,
            'last_access': self.last_access
        }
        return ret
