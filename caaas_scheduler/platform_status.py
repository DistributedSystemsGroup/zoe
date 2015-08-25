import time

from caaas_scheduler.swarm_status import SwarmStatus
from caaas_scheduler.periodic_tasks import periodic_task
from caaas_scheduler.swarm_client import SwarmClient

from common.status import PlatformStatusReport


class PlatformStatus:
    def __init__(self):
        self.swarm_status = SwarmStatus()
        self.swarm = SwarmClient()

    def update(self):
        self.swarm_status = self.swarm.info()

    def update_task(self, interval):
        self.update()
        periodic_task(self.update, interval)

    def generate_report(self) -> PlatformStatusReport:
        report = PlatformStatusReport()
        report.include_swarm_status(self.swarm_status)
        return report
