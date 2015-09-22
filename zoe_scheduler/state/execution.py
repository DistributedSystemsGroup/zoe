from datetime import datetime

from sqlalchemy import Column, Integer, String, PickleType, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from zoe_scheduler.state import Base


class ExecutionState(Base):
    __tablename__ = 'executions'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    assigned_resources = Column(PickleType())
    application_id = Column(Integer, ForeignKey('applications.id'))
    time_scheduled = Column(DateTime)
    time_started = Column(DateTime)
    time_finished = Column(DateTime)
    status = Column(String(32))
    termination_notice = Column(Boolean, default=False)

    cluster = relationship("ClusterState", uselist=False, backref="execution")

    def set_scheduled(self):
        self.status = "scheduled"
        self.time_scheduled = datetime.now()

    def set_started(self):
        self.status = "running"
        self.time_started = datetime.now()

    def set_finished(self):
        self.status = "finished"
        self.time_finished = datetime.now()

    def set_terminated(self):
        self.status = "terminated"
        self.time_finished = datetime.now()

    def find_container(self, name):
        for c in self.cluster.containers:
            if c.readable_name == name:
                return c

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'name': self.name,
            'application_id': self.application_id,
            'time_scheduled': self.time_scheduled,
            'time_started': self.time_started,
            'time_finished': self.time_finished,
            'status': self.status,
            'termination_notice': self.termination_notice,
        }

        if self.assigned_resources is None:
            ret['assigned_resources'] = None
        else:
            ret['assigned_resources'] = self.assigned_resources.to_dict()

        if self.cluster is not None:
            ret['cluster_id'] = self.cluster.id
            ret['containers'] = [c.to_dict() for c in self.cluster.containers]
        else:
            ret['cluster_id'] = None
            ret['containers'] = []

        return ret

    def gen_environment_substitution(self):
        ret = {}
        for cont in self.cluster.containers:
            ret[cont.readable_name] = {
                'ip_address': cont.ip_address
            }
        return ret
