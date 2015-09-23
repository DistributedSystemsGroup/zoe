import time

from zoe_scheduler.platform_status import PlatformStatus
from zoe_scheduler.stats import SchedulerStats
from zoe_scheduler.scheduler_policies.base import BaseSchedulerPolicy
from zoe_scheduler.application_description import ZoeApplication


class SimpleSchedulerPolicy(BaseSchedulerPolicy):
    def __init__(self, platform_status: PlatformStatus):
        self.platform_status = platform_status
        self.waiting_list = []
        self.running_list = []

    def admission_control(self, app_description: ZoeApplication) -> bool:
        if app_description.total_memory() < self.platform_status.swarm_status.memory_total:
            return True
        else:
            return False

    def execution_submission(self, execution_id: int, app_description: ZoeApplication):
        self.waiting_list.append((execution_id, app_description))

    def runnable_get(self) -> (int, ZoeApplication):
        try:
            exec_id, resources = self.waiting_list.pop(0)
        except IndexError:
            return None, None

        return exec_id, resources

    def stats(self):
        ret = SchedulerStats()
        ret.count_waiting = len(self.waiting_list)
        ret.timestamp = time.time()
        return ret
