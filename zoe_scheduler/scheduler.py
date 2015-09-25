import logging
import queue

from zoe_scheduler.application_description import ZoeApplication
from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.execution import ExecutionState
from zoe_scheduler.scheduler_policies.base import BaseSchedulerPolicy

log = logging.getLogger(__name__)


class ZoeScheduler:
    """
    :type platform: PlatformManager
    :type scheduler_policy: BaseSchedulerPolicy
    """
    def __init__(self):
        self.platform = None
        self.scheduler_policy = None
        self.event_queue = queue.Queue()

    def set_policy(self, policy_class):
        """
        This method is called during initialization, it instantiates the policy class that will be used for scheduling executions.
        :param policy_class: The policy class the will be used for scheduling
        :return: None
        """
        self.scheduler_policy = policy_class(self.platform.status)

    def validate(self, app_description: ZoeApplication) -> bool:
        """
        This method is called in the IPC thread context. It is used to validate an execution that is going to be started.
        :param app_description:
        :return: True if the execution is possible on this Zoe deployment, False otherwise
        """
        return self.scheduler_policy.admission_control(app_description)

    def incoming(self, execution: ExecutionState):
        """
        This method is called in the IPC thread context. It passes the execution request ID and the requested resources to the scheduling policy.
        Execution is guaranteed to start (sometime in the future) if the execution validation for this application description returned True.
        :param execution: The execution request
        :return:
        """
        self.event_queue.put(("submission", (execution.id, execution.app_description)))

    def execution_terminate(self, state: AlchemySession, execution: ExecutionState) -> None:
        """
        This method is called in the IPC thread context. It terminates the given execution.
        :param state: SQLAlchemy session containing the scheduler state
        :param execution: the execution to terminate
        :return: None
        """
        self.platform.execution_terminate(execution)
        self.event_queue.put(("termination", execution.id))

    def _check_runnable(self):  # called periodically, does not use state
        """
        This method is called by the main scheduler loop to check if there is an execution that can be run. In case there is
        it starts it.
        :return: None
        """
        execution_id, app_description = self.scheduler_policy.runnable_get()
        if execution_id is None:
            return
        log.debug("Found a runnable execution!")
        success = self.platform.start_execution(execution_id, app_description)
        if not success:  # Some error happened
            log.error('Execution ID {} cannot be started'.format(execution_id))

    def loop(self):
        """
        This method is the scheduling task. It is the loop the main thread runs, started from the zoe-scheduler executable.
        It does not use an sqlalchemy session.
        :return: None
        """
        while True:
            try:
                event, data = self.event_queue.get()
                if event == "termination":
                    pass
                elif event == "submission":
                    execution_id = data[0]
                    app_descr = data[1]
                    self.scheduler_policy.execution_submission(execution_id, app_descr)
                else:
                    log.error("Unknown event received")
                self.event_queue.task_done()

                self._check_runnable()  # Check if an execution can be started
            except KeyboardInterrupt as e:
                raise e
            except:
                log.exception("Uncaught exception in scheduler loop")
