import logging

from zoe_scheduler.stats import PlatformStats
from zoe_scheduler.swarm_client import SwarmClient

log = logging.getLogger(__name__)


class PlatformStatus:
    def __init__(self, scheduler):
        self.swarm = SwarmClient()
        self.swarm_status = None
        self.scheduler = scheduler
        self.scheduler_status = None

    def update(self):
        self.swarm_status = self.swarm.info()
        self.scheduler_status = self.scheduler.scheduler_policy.stats()

    def stats(self):
        ret = PlatformStats()
        ret.scheduler = self.scheduler_status
        ret.swarm = self.swarm_status
        return ret
