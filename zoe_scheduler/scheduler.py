import logging
from threading import Barrier
import time

from zoe_scheduler.platform import PlatformManager
from zoe_scheduler.platform_status import PlatformStatus
from zoe_scheduler.periodic_tasks import PeriodicTaskManager
from zoe_scheduler.proxy_manager import proxy_manager
from common.configuration import zoeconf
from zoe_scheduler.state.execution import ExecutionState
from common.application_resources import ApplicationResources
from zoe_scheduler.stats import SchedulerStats

log = logging.getLogger(__name__)


class SimpleSchedulerPolicy:
    def __init__(self, platform_status: PlatformStatus):
        self.platform_status = platform_status
        self.waiting_list = []
        self.running_list = []

    def admission_control(self, required_resources: ApplicationResources) -> bool:
        if required_resources.core_count() < self.platform_status.swarm_status.cores_total:
            return True
        else:
            return False

    def insert(self, execution_id: int, resources: ApplicationResources):
        self.waiting_list.append((execution_id, resources))

    def runnable(self) -> (int, ApplicationResources):
        try:
            exec_id, resources = self.waiting_list.pop(0)
        except IndexError:
            return None, None

        assigned_resources = resources  # Could modify the amount of resource assigned before running
        return exec_id, assigned_resources

    def started(self, execution_id: int, resources: ApplicationResources):
        self.running_list.append((execution_id, resources))

    def terminated(self, execution_id: int):
        if self.find_execution_running(execution_id):
            self.running_list = [x for x in self.running_list if x[0] != execution_id]
        if self.find_execution_waiting(execution_id):
            self.waiting_list = [x for x in self.waiting_list if x[0] != execution_id]

    def find_execution_running(self, exec_id) -> bool:
        for e, r in self.running_list:
            if e == exec_id:
                return True
        return False

    def find_execution_waiting(self, exec_id) -> bool:
        for e, r in self.waiting_list:
            if e == exec_id:
                return True
        else:
            return False

    def stats(self):
        ret = SchedulerStats()
        ret.count_running = len(self.running_list)
        ret.count_waiting = len(self.waiting_list)
        ret.timestamp = time.time()
        return ret


class ZoeScheduler:
    def __init__(self):
        self.platform = PlatformManager()
        self.platform_status = PlatformStatus(self)
        self.scheduler_policy = SimpleSchedulerPolicy(self.platform_status)

    def init_tasks(self, tm: PeriodicTaskManager) -> Barrier:
        barrier = Barrier(4)  # number of tasks + main thread
        tm.add_task("platform status updater", self.platform_status.update, zoeconf().interval_status_refresh, barrier)
        tm.add_task("proxy access timestamp updater", proxy_manager().update_proxy_access_timestamps, zoeconf().interval_proxy_update_accesses, barrier)
        tm.add_task("execution health checker", self.platform.check_executions_health, zoeconf().interval_check_health, barrier)
        return barrier

    def incoming(self, execution: ExecutionState) -> bool:
        if not self.scheduler_policy.admission_control(execution.application.required_resources):
            return False
        self.scheduler_policy.insert(execution.id, execution.application.required_resources)
        return True

    def _check_runnable(self):  # called periodically, does not use state to keep database load low
        execution_id, resources = self.scheduler_policy.runnable()
        if execution_id is None:
            return
        log.debug("Found a runnable execution!")
        if self.platform.start_execution(execution_id, resources):
            self.scheduler_policy.started(execution_id, resources)
        else:  # Some error happened
            log.error('Execution ID {} cannot be started'.format(execution_id))

    def loop(self):  # FIXME the scheduler should wait on events, not sleep
        """
        This method is the scheduling task. It is the loop the main thread runs, started from the zoe-scheduler executable.
        It does not use an sqlalchemy session.
        :return: None
        """
        while True:
            self.schedule()
            time.sleep(zoeconf().interval_scheduler_task)

    def schedule(self):
        self._check_runnable()

    def execution_terminate(self, state, execution: ExecutionState):
        self.platform.execution_terminate(state, execution)
        self.scheduler_policy.terminated(execution.id)
