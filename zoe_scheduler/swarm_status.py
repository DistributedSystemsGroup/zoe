import time


class SwarmNodeStatus:
    def __init__(self, name):
        self.name = name
        self.docker_endpoint = None
        self.container_count = 0
        self.cores_total = 0
        self.cores_reserved = 0
        self.memory_total = 0
        self.memory_reserved = 0
        self.labels = {}

    def to_dict(self):
        return {
            'name': self.name,
            'docker_endpoint': self.docker_endpoint,
            'container_count': self.container_count,
            'cores_total': self.cores_total,
            'cores_reserved': self.cores_reserved,
            'memory_total': self.memory_total,
            'memory_reserved': self.memory_reserved,
            'labels': self.labels.copy()
        }


class SwarmStatus:
    def __init__(self):
        self.container_count = 0
        self.image_count = 0
        self.memory_total = 0
        self.cores_total = 0
        self.placement_strategy = ''
        self.active_filters = []
        self.nodes = []
        self.timestamp = time.time()

    def to_dict(self):
        ret = {
            'container_count': self.container_count,
            'image_count': self.image_count,
            'memory_total': self.memory_total,
            'cores_total': self.cores_total,
            'placement_strategy': self.placement_strategy,
            'active_filters': self.active_filters.copy(),
            'timestamp': self.timestamp,
            'nodes': [x.to_dict() for x in self.nodes]
        }
        return ret
