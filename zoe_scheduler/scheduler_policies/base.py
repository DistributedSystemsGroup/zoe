# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from zoe_scheduler.state.application import Application
from zoe_scheduler.state.execution import Execution
from zoe_scheduler.stats import SchedulerStats


class BaseSchedulerPolicy:
    def __init__(self, platform):
        self.platform = platform

    def admission_control(self, app: Application) -> bool:
        """
        Checks whether an execution requiring the specified resources can be run, now or at a later time. This method can be called
        from outside the scheduler thread, should not have any side effects nor change any state.
        :param app: an application description object describing the resources required by the execution
        :return: True if the execution is possible, False otherwise
        """
        raise NotImplementedError

    def execution_submission(self, execution: Execution) -> None:
        """
        A new execution request has been submitted and needs to scheduled. The request has passed admission control.
        :param execution: the execution to start
        :return:
        """
        raise NotImplementedError

    def execution_kill(self, execution: Execution) -> None:
        """
        An execution has been killed, most probably by the user. Cleanup any status associated with that execution.
        :param execution: the terminated execution
        :return:
        """
        raise NotImplementedError

    def runnable_get(self) -> Execution:
        """
        Fetches an execution that can be run right now. It can modify the application description that is returned,
        respecting the minimums required by the application.
        :return: a tuple (execution, application), or (None, None) if no execution can be started
        """
        raise NotImplementedError

    def stats(self) -> SchedulerStats:
        """
        Gather statistics about the scheduler policy
        :return: a SchedulerStats object
        """
        raise NotImplementedError
