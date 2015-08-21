import rpyc

from caaas_scheduler.scheduler import caaas_sched

from common.status import PlatformStatusReport
from common.state import AlchemySession, Application


class CAaaSSchedulerRPCService(rpyc.Service):
    sched = caaas_sched

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def exposed_get_platform_status(self) -> PlatformStatusReport:
        pl_status = self.sched.platform_status.generate_report()
        return pl_status

    def exposed_terminate_application(self, application_id: int):
        state = AlchemySession()
        application = state.query(Application).filter_by(id=application_id).one()
        self.sched.terminate_application(application)
        state.commit()
        return True
