from docker import Client
from threading import Thread
import time


class SwarmStatus:
    def __init__(self):
        self.num_nodes = 0
        self.num_containers = 0


class Swarm:
    def __init__(self):
        self.status = SwarmStatus()
        self.cli = None
        self.manager = None

    def connect(self, swarm_manager):
        self.manager = swarm_manager
        self.cli = Client(base_url="tcp://" + self.manager)

    def start_update_thread(self):
        assert self.manager is not None
        th = Thread(target=self._thread_cb)
        th.start()

    def _thread_cb(self):
        print("Stats update thread started")
        while True:
            self.update_status()
            time.sleep(1)

    def update_status(self):
        assert self.cli is not None
        info = self.cli.info()
        self.status.num_containers = info["Containers"]
        self.status.num_nodes = info["DriverStatus"][3][1]

swarm = Swarm()
