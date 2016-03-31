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


class Stats:
    def __init__(self):
        self.timestamp = None

    def to_dict(self) -> dict:
        ret = {}
        ret.update(vars(self))
        return ret


class SwarmNodeStats(Stats):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.docker_endpoint = None
        self.container_count = 0
        self.cores_total = 0
        self.cores_reserved = 0
        self.memory_total = 0
        self.memory_reserved = 0
        self.labels = {}


class SwarmStats(Stats):
    def __init__(self):
        super().__init__()
        self.container_count = 0
        self.image_count = 0
        self.memory_total = 0
        self.cores_total = 0
        self.placement_strategy = ''
        self.active_filters = []
        self.status = 'Unknown'
        self.nodes = []

    def to_dict(self) -> dict:
        ret = {
            'container_count': self.container_count,
            'image_count': self.image_count,
            'memory_total': self.memory_total,
            'cores_total': self.cores_total,
            'placement_strategy': self.placement_strategy,
            'active_filters': self.active_filters,
            'nodes': []
        }
        for node in self.nodes:
            ret['nodes'].append(node.to_dict())

        return ret


class SchedulerStats(Stats):
    def __init__(self):
        super().__init__()
        self.count_waiting = 0
        self.waiting_list = []
