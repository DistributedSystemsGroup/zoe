import asyncio

from caaas_scheduler.platform import PlatformManager
from caaas_scheduler.platform_status import PlatformStatus
from caaas_scheduler.periodic_tasks import periodic_task

from common.configuration import conf
from common.state import Application, Execution
from common.application_resources import ApplicationResources


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


class CAaaSSCheduler:
    def __init__(self):
        self.platform = PlatformManager()
        self.platform_status = PlatformStatus()
        self.scheduler_policy = SimpleSchedulerPolicy(self.platform_status)

    def init_tasks(self):
        self.platform_status.update_task(conf["status_refresh_interval"])
        periodic_task(self.schedule, conf['scheduler_task_interval'])

    def incoming(self, execution: Execution) -> bool:
        if not self.scheduler_policy.admission_control(execution.application.required_resources):
            return False
        self.scheduler_policy.insert(execution.id, execution.application.required_resources)
        asyncio.get_event_loop().call_soon(self._check_runnable)
        return True

    def _check_runnable(self):  # called periodically, does not use state to keep database load low
        execution_id, resources = self.scheduler_policy.runnable()
        if execution_id is None:
            return

        if self.platform.start_execution(execution_id, resources):
            self.scheduler_policy.started(execution_id, resources)

    def schedule(self):
        self._check_runnable()

    def terminate_execution(self, execution: Execution):
        self.platform.terminate_execution(execution)
        self.scheduler_policy.terminated(execution.id)


caaas_sched = CAaaSSCheduler()
