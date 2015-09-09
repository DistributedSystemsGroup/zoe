import time

from common.state import ApplicationState, ExecutionState, ContainerState, ProxyState


class Stats:
    def __init__(self):
        self.timestamp = None


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

    def __str__(self):
        s = " -- Node {}\n".format(self.name)
        s += " -- Docker endpoint: {}\n".format(self.docker_endpoint)
        s += " -- Container count: {}\n".format(self.container_count)
        s += " -- Memory total: {}\n".format(self.memory_total)
        s += " -- Memory reserved: {}\n".format(self.memory_reserved)
        s += " -- Cores total: {}\n".format(self.cores_total)
        s += " -- Cores reserved: {}\n".format(self.cores_reserved)
        s += " -- Labels: {}\n".format(self.labels)
        return s


class SwarmStats(Stats):
    def __init__(self):
        super().__init__()
        self.container_count = 0
        self.image_count = 0
        self.memory_total = 0
        self.cores_total = 0
        self.placement_strategy = ''
        self.active_filters = []
        self.nodes = []

    def __str__(self):
        s = " - Container count: {}\n".format(self.container_count)
        s += " - Image count: {}\n".format(self.image_count)
        s += " - Memory total: {}\n".format(self.memory_total)
        s += " - Cores total: {}\n".format(self.cores_total)
        s += " - Placement strategy: {}\n".format(self.placement_strategy)
        s += " - Active filters: {}\n".format(self.active_filters)
        for node in self.nodes:
            s += str(node)
        return s


class SchedulerStats(Stats):
    def __init__(self):
        super().__init__()
        self.count_running = 0
        self.count_waiting = 0

    def __str__(self):
        return " - Apps running: {}\n - Apps waiting: {}\n".format(self.count_running, self.count_waiting)


class PlatformStats(Stats):
    def __init__(self):
        super().__init__()
        self.swarm = SwarmStats()
        self.scheduler = SchedulerStats()

    def __str__(self):
        return "Swarm:\n{}\nScheduler:\n{}\n".format(self.swarm, self.scheduler)
