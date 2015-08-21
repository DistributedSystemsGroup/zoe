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


class SwarmStatus:
    def __init__(self):
        self.container_count = 0
        self.image_count = 0
        self.memory_total = 0
        self.cores_total = 0
        self.placement_strategy = ''
        self.active_filters = []
        self.nodes = []
