# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime

from sqlalchemy import Column, Integer, String, PickleType, DateTime
from sqlalchemy.orm import relationship

from zoe_scheduler.state import Base


class ExecutionState(Base):
    __tablename__ = 'executions'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    app_description = Column(PickleType())
    application_id = Column(Integer)
    time_scheduled = Column(DateTime)
    time_started = Column(DateTime)
    time_finished = Column(DateTime)
    status = Column(String(32))

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

    def set_cleaning_up(self):
        self.status = "cleaning up"

    def set_terminated(self):
        self.status = "terminated"
        self.time_finished = datetime.now()

    def find_container(self, name):
        for c in self.cluster.containers:
            if c.description.name == name:
                return c

    def to_dict(self) -> dict:
        ret = {
            'id': self.id,
            'name': self.name,
            'application_id': self.application_id,
            'time_scheduled': self.time_scheduled,
            'time_started': self.time_started,
            'time_finished': self.time_finished,
            'status': self.status
        }

        if self.app_description is None:
            ret['app_description'] = None
        else:
            ret['app_description'] = self.app_description.to_dict()

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
            ret[cont.description.name] = {
                'ip_address': cont.ip_address
            }
        return ret
