# Copyright (c) 2017, Daniele Venzano
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

"""The base class for Zoe schedulers"""

import zoe_lib.state


class ZoeBaseScheduler:
    """The base class for Zoe schedulers"""

    def __init__(self, state: zoe_lib.state.SQLManager):
        self.state = state

    def trigger(self):
        """Trigger a scheduler run."""
        raise NotImplementedError

    def admission_control(self, execution: zoe_lib.state.Execution):
        """
        Checks if the execution can be admitted to the scheduler, comparing with user quotas.
        If the execution passes, incoming() is called, an exception is raised otherwise.

        :param execution: the candidate execution
        :return:
        """
        user = self.state.user_list(only_one=True, id=execution.user_id)
        quota = self.state.quota_list(only_one=True, id=user.quota_id)
        if execution.total_reservations['memory'] > quota.memory:
            execution.set_error_message('Memory reservation over total quota size')
            execution.set_error()
            return
        if execution.total_reservations['cores'] > quota.cores:
            execution.set_error_message('Cores reservation over total quota size')
            execution.set_error()
            return

        user_execs = self.state.execution_list(user_id=user.id, status='running')
        user_execs += self.state.execution_list(user_id=user.id, status='starting')
        user_execs += self.state.execution_list(user_id=user.id, status='scheduled')
        user_execs = [e for e in user_execs if e != execution]  # this one will be in scheduled state

        if len(user_execs) + 1 > quota.concurrent_executions:
            execution.set_error_message('Reached the quota limit for concurrent executions')
            execution.set_error()
            return

        reserved_memory = sum([e.total_reservations['memory'] for e in user_execs])
        if reserved_memory + execution.total_reservations['memory'] > quota.memory:
            execution.set_error_message('Memory reservation over total quota size')
            execution.set_error()
            return

        reserved_cores = sum([e.total_reservations['cores'] for e in user_execs])
        if reserved_cores + execution.total_reservations['cores'] > quota.cores:
            execution.set_error_message('Cores reservation over total quota size')
            execution.set_error()
            return

        self.incoming(execution)

    def incoming(self, execution: zoe_lib.state.Execution):
        """
        This method adds the execution to the end of the FIFO queue and triggers the scheduler.
        :param execution: The execution
        :return:
        """
        raise NotImplementedError

    def terminate(self, execution: zoe_lib.state.Execution) -> None:
        """
        Inform the master that an execution has been terminated. This can be done asynchronously.
        :param execution: the terminated execution
        :return: None
        """
        raise NotImplementedError

    def quit(self):
        """Stop the scheduler."""
        raise NotImplementedError

    def stats(self):
        """Scheduler statistics."""
        raise NotImplementedError
