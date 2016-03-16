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

from zoe_lib.exceptions import ZoeException
from zoe_master.state.base import BaseState
from zoe_master.state.execution import Execution


class Container(BaseState):
    """
    :type docker_id: str
    :type execution: Execution
    :type ip_address: str
    """

    api_out_attrs = ['docker_id', 'ip_address', 'name', 'is_monitor', 'ports']

    def __init__(self, state):
        super().__init__(state)

        self.docker_id = ''
        self.ip_address = ''
        self.name = ''
        self.is_monitor = False

        self.execution = None
        self.ports = None

    def to_dict(self, checkpoint):
        d = super().to_dict(checkpoint)

        d['execution_id'] = self.execution.id
        return d

    def from_dict(self, d, checkpoint):
        super().from_dict(d, checkpoint)

        e = self.state_manger.get_one('execution', id=d['execution_id'])
        if e is None:
            raise ZoeException('Deserialized Container points to a non-existent execution')
        self.execution = e
        e.containers.append(self)

    @property
    def owner(self):
        return self.execution.user
