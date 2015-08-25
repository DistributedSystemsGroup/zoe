import rpyc

from caaas_scheduler.scheduler import caaas_sched

from common.status import PlatformStatusReport, ApplicationStatusReport
from common.state import AlchemySession, Application, Execution


class CAaaSSchedulerRPCService(rpyc.Service):
    sched = caaas_sched

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def exposed_get_platform_status(self) -> PlatformStatusReport:
        pl_status = self.sched.platform_status.generate_report()
        return pl_status

    def exposed_terminate_execution(self, execution_id: int) -> bool:
        state = AlchemySession()
        execution = state.query(Execution).filter_by(id=execution_id).one()
        self.sched.terminate_execution(execution)
        state.commit()
        return True

    def exposed_execution_schedule(self, execution_id: int) -> bool:
        state = AlchemySession()
        execution = state.query(Execution).filter_by(id=execution_id).one()
        ret = self.sched.incoming(execution)
        if ret:
            execution.set_scheduled()
            state.commit()
        return ret

    def exposed_application_status(self, application_id: int):
        state = AlchemySession()
        application = state.query(Application).filter_by(id=application_id).one()
        report = ApplicationStatusReport(application)
        for e in application.executions:
            report.add_execution(e)
        return report
