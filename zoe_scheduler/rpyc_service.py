import rpyc
from sqlalchemy.orm.exc import NoResultFound

from zoe_scheduler.scheduler import zoe_sched

from common.stats import PlatformStats
from common.state import AlchemySession, ContainerState
from common.state.execution import ExecutionState


class ZoeSchedulerRPCService(rpyc.Service):
    sched = zoe_sched

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def exposed_execution_schedule(self, execution_id: int) -> bool:
        state = AlchemySession()
        execution = state.query(ExecutionState).filter_by(id=execution_id).one()
        ret = self.sched.incoming(execution)
        if ret:
            execution.set_scheduled()
            state.commit()
        return ret

    def exposed_execution_terminate(self, execution_id: int) -> bool:
        state = AlchemySession()
        execution = state.query(ExecutionState).filter_by(id=execution_id).one()
        self.sched.execution_terminate(state, execution)
        state.commit()
        return True

    def exposed_log_get(self, container_id: int) -> str:
        state = AlchemySession()
        try:
            container = state.query(ContainerState).filter_by(id=container_id).one()
        except NoResultFound:
            return None

        return self.sched.platform.log_get(container)

    def exposed_platform_stats(self) -> PlatformStats:
        return self.sched.platform_status.stats()
