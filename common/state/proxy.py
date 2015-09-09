from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func

from common.state import Base


class ProxyState(Base):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)
    internal_url = Column(String(1024))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    container_id = Column(Integer, ForeignKey('containers.id'))
    service_name = Column(String(32))
    last_access = Column(DateTime, default=func.now())

    def extract(self):
        return Proxy(self)


class Proxy:
    def __init__(self, proxy: ProxyState):
        self.id = proxy.id
        self.internal_url = proxy.internal_url
        self.cluster_id = proxy.cluster_id
        self.container_id = proxy.container_id
        self.service_name = proxy.service_name
        self.last_access = proxy.last_access
