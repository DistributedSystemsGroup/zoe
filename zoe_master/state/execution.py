# Copyright (c) 2016, Daniele Venzano
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

import zipfile
from datetime import datetime
from io import BytesIO

import dateutil.parser

from zoe_master.state.base import BaseState
from zoe_master.state.application import ApplicationDescription
from zoe_lib.exceptions import ZoeException


def deserialize_datetime(isoformat):
    if isoformat is None:
        return None
    else:
        return dateutil.parser.parse(isoformat)


class Execution(BaseState):

    api_in_attrs = ['name', 'application']
    api_out_attrs = ['name', 'application', 'status', 'time_scheduled', 'time_started', 'time_finished']

    def __init__(self, state):
        super().__init__(state)

        self.name = ''
        self.time_scheduled = None
        self.time_started = None
        self.time_finished = None
        self.status = 'undefined'

        # Links to other objects
        self.user = None
        self.application = None
        self.services = []

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

    def set_error(self):
        self.status = 'error'
        self.time_finished = datetime.now()

    def is_active(self):
        return self.status == 'scheduled' or self.status == 'running'

    def to_dict(self, checkpoint):
        d = super().to_dict(checkpoint)
        for attr in ['time_scheduled', 'time_started', 'time_finished']:
            if getattr(self, attr) is not None:
                d[attr] = getattr(self, attr).isoformat()
            else:
                d[attr] = None
        d['application'] = self.application.to_dict()

        if not checkpoint:
            d['services'] = [c.id for c in self.services]
        else:
            d['user_id'] = self.user.id

        return d

    def from_dict(self, d, checkpoint):
        super().from_dict(d, checkpoint)
        if checkpoint:
            for attr in ['time_scheduled', 'time_started', 'time_finished']:
                if d[attr] is not None:
                    setattr(self, attr, deserialize_datetime(getattr(self, attr)))
                else:
                    setattr(self, attr, None)

        app = ApplicationDescription()
        app.from_dict(d['application'])
        self.application = app

        user = self.state_manger.get_one('user', id=d['user_id'])
        if user is None:
            raise ZoeException('Deserialized execution points to a non-existent user')
        self.user = user
        user.executions.append(self)

    @property
    def owner(self):
        return self.user
