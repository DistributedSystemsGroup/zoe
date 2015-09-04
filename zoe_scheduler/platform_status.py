import logging
log = logging.getLogger(__name__)

from zoe_scheduler.swarm_status import SwarmStatus
from zoe_scheduler.swarm_client import SwarmClient

from common.status import PlatformStatusReport


class PlatformStatus:
    def __init__(self):
        self.swarm_status = SwarmStatus()
        self.swarm = SwarmClient()

    def update(self):
        self.swarm_status = self.swarm.info()

    def generate_report(self) -> PlatformStatusReport:
        report = PlatformStatusReport()
        report.include_swarm_status(self.swarm_status)
        return report
