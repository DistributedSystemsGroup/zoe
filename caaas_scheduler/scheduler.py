from caaas_scheduler.platform import PlatformManager
from caaas_scheduler.platform_status import PlatformStatus

from common.configuration import conf
from common.state import Application
from common.application_resources import ApplicationResources


class SimpleSchedulerPolicy:
    def __init__(self, platform_status: PlatformStatus):
        self.platform_status = platform_status
        self.applications_waiting = []
        self.applications_running = []

    def admission_control(self, application: Application) -> bool:
        if application.requirements.core_count() < self.platform_status.swarm_status.cores_total:
            return True
        else:
            return False

    def insert(self, application: Application):
        self.applications_waiting.append(application)

    def runnable(self) -> (Application, ApplicationResources):
        try:
            app = self.applications_waiting.pop(0)
        except IndexError:
            return None, None

        assigned_resources = app.requirements  # Could modify the amount of resource actually used
        return app, assigned_resources

    def started(self, application: Application):
        self.applications_running.append(application)

    def terminated(self, application: Application):
        if application in self.applications_running:
            self.applications_running.remove(application)
        if application in self.applications_waiting:
            self.applications_waiting.remove(application)


class CAaaSSCheduler:
    def __init__(self):
        self.platform = PlatformManager()
        self.platform_status = PlatformStatus()
        self.scheduler_policy = SimpleSchedulerPolicy(self.platform_status)

    def init_tasks(self):
        self.platform_status.update_task(conf["status_refresh_interval"])

    def incoming_application(self, application: Application):
        if not self.scheduler_policy.admission_control(application):
            return False
        self.scheduler_policy.insert(application)
        self.check_runnable()

    def check_runnable(self):
        application, resources = self.scheduler_policy.runnable()
        if application is None:
            return

        self.platform.start_application(application, resources)
        self.scheduler_policy.started(application)

    def terminate_application(self, application: Application):
        self.platform.terminate_application(application)
        self.scheduler_policy.terminated(application)


caaas_sched = CAaaSSCheduler()
