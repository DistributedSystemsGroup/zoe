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
        self.cores_free = 0
        self.memory_total = 0
        self.memory_reserved = 0
        self.memory_free = 0
        self.labels = {}
        self.status = None
        self.error = ''

    def serialize(self):
        """Convert the object into a dict."""
        return {
            'name': self.name,
            'container_count': self.container_count,
            'cores_total': self.cores_total,
            'cores_reserved': self.cores_reserved,
            'cores_free': self.cores_free,
            'memory_total': self.memory_total,
            'memory_reserved': self.memory_reserved,
            'memory_free': self.memory_free,
            'labels': self.labels,
            'status': self.status,
            'error': self.error
        }


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
    def container_count(self) -> int:
        """Total number of containers."""
        return sum([node.container_count for node in self.nodes])
