from sqlalchemy import Column, Integer, String, ForeignKey

from common.state import Base


class Container(Base):
    __tablename__ = 'containers'

    id = Column(Integer, primary_key=True)
    docker_id = Column(String(128))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    ip_address = Column(String(16))
    readable_name = Column(String(32))

    def __repr__(self):
        return "<Container(name='%s', id='%s', docker_id='%s', cluster_id='%s', ip_address='%s')>" % (
            self.readable_name, self.id, self.docker_id, self.cluster_id, self.ip_address)
