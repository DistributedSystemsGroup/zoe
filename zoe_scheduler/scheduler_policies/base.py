from common.application_description import ZoeApplication
from zoe_scheduler.stats import SchedulerStats


class BaseSchedulerPolicy:
    def admission_control(self, app_description: ZoeApplication) -> bool:
        """
        Checks whether an execution requiring the specified resources can be run, now or at a later time. This method can be called
        from outside the scheduler thread, should not have any side effects nor change any state.
        :param app_description: an application description object describing the resources required by the execution
        :return: True if the execution is possible, False otherwise
        """
        raise NotImplementedError

    def execution_submission(self, execution_id: int, app_description: ZoeApplication) -> None:
        """
        A new execution request has been submitted and needs to scheduled. The request has passed admission control.
        :param execution_id: a unique identifier for this execution request
        :param app_description: the application to be executed
        :return: None
        """
        raise NotImplementedError

    def runnable_get(self) -> (int, ZoeApplication):
        """
        Fetches an execution that can be run right now. It can modify the application description that is returned,
        respecting the minimums required by the application.
        :return: a tuple (execution_id, application description), or (None, None) if no execution can be started
        """
        raise NotImplementedError

    def stats(self) -> SchedulerStats:
        """
        Gather statistics about the scheduler policy
        :return: a SchedulerStats object
        """
        raise NotImplementedError
