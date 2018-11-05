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

"""This module contains classes for statistics on various entities in the Zoe master."""

import time


class Stats:
    """Base statistics class.

    Every Stats object must have a timestamp that records when the stats it contains where recorded.
    """
    def __init__(self):
        self.timestamp = time.time()


class NodeStats(Stats):
    """Stats related to a single node."""
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.container_count = 0
        self.cores_total = 0
        self.cores_reserved = 0
        self.cores_allocated = 0
        self.cores_in_use = 0
        self.memory_total = 0
        self.memory_allocated = 0
        self.memory_reserved = 0
        self.memory_in_use = 0
        self.labels = []
        self.status = 'offline'
        self.service_stats = {}
        self.images = []
        self.valid = False

    def serialize(self):
        """Convert the object into a dict."""
        ret = {
            'name': self.name,
            'container_count': self.container_count,
            'cores_total': self.cores_total,
            'cores_reserved': self.cores_reserved,
            'cores_allocated': self.cores_allocated,
            'cores_in_use': self.cores_in_use,
            'memory_total': self.memory_total,
            'memory_reserved': self.memory_reserved,
            'memory_allocated': self.memory_allocated,
            'memory_in_use': self.memory_in_use,
            'labels': list(self.labels),
            'status': self.status,
            'service_stats': self.service_stats,
            'images': self.images
        }
        return ret


class ClusterStats(Stats):
    """Stats related to the whole cluster."""
    def __init__(self):
        super().__init__()
        self.nodes = []

    def serialize(self):
        """Convert the object into a dict."""
        return {
            'container_count': self.container_count,
            'memory_total': self.memory_total,
            'cores_total': self.cores_total,
            'memory_reserved': sum([n.memory_reserved for n in self.nodes]),
            'cores_reserved': sum([n.cores_reserved for n in self.nodes]),
            'memory_in_use': sum([n.memory_in_use for n in self.nodes]),
            'cores_in_use': sum([n.cores_in_use for n in self.nodes]),
            'nodes': [x.serialize() for x in self.nodes]
        }

    @property
    def memory_total(self) -> int:
        """Total memory installed in the whole platform."""
        return sum([node.memory_total for node in self.nodes])

    @property
    def cores_total(self) -> int:
        """Total number of cores installed."""
        return sum([node.cores_total for node in self.nodes])

    @property
    def memory_reserved(self) -> int:
        """Total memory reserved in the whole platform."""
        return sum([node.memory_reserved for node in self.nodes])

    @property
    def cores_reserved(self) -> int:
        """Total number of cores reserved."""
        return sum([node.cores_reserved for node in self.nodes])

    @property
    def memory_in_use(self) -> int:
        """Total memory in use in the whole platform."""
        return sum([node.memory_in_use for node in self.nodes])

    @property
    def cores_in_use(self) -> int:
        """Total number of cores in use."""
        return sum([node.cores_in_use for node in self.nodes])

    @property
    def container_count(self) -> int:
        """Total number of containers."""
        return sum([node.container_count for node in self.nodes])
