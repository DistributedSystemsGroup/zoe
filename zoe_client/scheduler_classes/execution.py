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

import dateutil.parser

from zoe_client.scheduler_classes.container import Container

from common.application_description import ZoeApplication


def deserialize_datetime(isoformat):
    if isoformat is None:
        return None
    else:
        return dateutil.parser.parse(isoformat)


class Execution:
    """
    :type app_description: ZoeApplication
    """
    def __init__(self, execution: dict):
        self.id = execution['id']
        self.name = execution['name']
        self.app_description = ZoeApplication.from_dict(execution['app_description'])
        self.application_id = execution['application_id']
        self.time_started = deserialize_datetime(execution['time_started'])
        self.time_scheduled = deserialize_datetime(execution['time_scheduled'])
        self.time_finished = deserialize_datetime(execution['time_finished'])
        self.status = execution['status']
        self.cluster_id = execution['cluster_id']

        self.containers = []

        for c in execution['containers']:
            self.containers.append(Container(c))
