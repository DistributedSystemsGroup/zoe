import rpyc
from sqlalchemy.orm.exc import NoResultFound

from zoe_scheduler.scheduler import zoe_sched

from common.status import PlatformStatusReport, ApplicationStatusReport
from common.state import AlchemySession, Application, Execution, Container


class ZoeSchedulerRPCService(rpyc.Service):
    sched = zoe_sched

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
        self.sched.terminate_execution(state, execution)
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

    def exposed_application_status(self, application_id: int) -> ApplicationStatusReport:
        state = AlchemySession()
        application = state.query(Application).filter_by(id=application_id).one()
        report = ApplicationStatusReport(application)
        for e in application.executions:
            report.add_execution(e)
        return report

    def exposed_log_get(self, container_id: int) -> str:
        state = AlchemySession()
        try:
            container = state.query(Container).filter_by(id=container_id).one()
        except NoResultFound:
            return None

        return self.sched.platform.log_get(container)
