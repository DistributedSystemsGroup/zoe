from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func

from common.state import Base


class Proxy(Base):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)
    internal_url = Column(String(1024))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    container_id = Column(Integer, ForeignKey('containers.id'))
    service_name = Column(String(32))
    last_access = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Proxy(service_name='%s', id='%s', internal_url='%s', cluster_id='%s', container_id='%s', last_access='%s')>" % (
            self.service_name, self.id, self.internal_url, self.cluster_id, self.container_id, self.last_access)
