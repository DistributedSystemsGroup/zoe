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

import logging
import queue

from zoe_scheduler.state.application import Application
from zoe_scheduler.state.execution import Execution
from zoe_scheduler.scheduler_policies.base import BaseSchedulerPolicy

log = logging.getLogger(__name__)


class ZoeScheduler:
    """
    :type platform: PlatformManager
    :type scheduler_policy: BaseSchedulerPolicy
    """
    def __init__(self, platform_manager, policy_class):
        self.platform = platform_manager
        self.event_queue = queue.Queue()
        self.scheduler_policy = policy_class(self.platform)

    def set_policy(self, policy_class):
        """
        This method is called during initialization, it instantiates the policy class that will be used for scheduling executions.
        :param policy_class: The policy class the will be used for scheduling
        :return: None
        """
        self.scheduler_policy = policy_class(self.platform.status)

    def validate(self, app: Application) -> bool:
        """
        It is used to validate an execution that is going to be started.
        :param app:
        :return: True if the execution is possible on this Zoe deployment, False otherwise
        """
        return self.scheduler_policy.admission_control(app)

    def incoming(self, execution: Execution):
        """
        This method passes the execution request to the scheduling policy.
        :param execution: The execution request
        :return:
        """
        self.scheduler_policy.execution_submission(execution)
        self._check_runnable()  # Check if an execution can be started

    def execution_terminate(self, execution: Execution) -> None:
        """
        Inform the scheduler that an execution has been terminated.
        :param execution: the terminated execution
        :return: None
        """
        self.scheduler_policy.execution_kill(execution)
        self._check_runnable()  # Check if an execution can be started

    def _check_runnable(self):  # called periodically, does not use state
        """
        This method is called by the main scheduler loop to check if there is an execution that can be run. In case there is
        it starts it.
        :return: None
        """
        execution = self.scheduler_policy.runnable_get()
        if execution is None:
            return
        log.debug("Found a runnable execution!")
        self.platform.execution_start(execution)
