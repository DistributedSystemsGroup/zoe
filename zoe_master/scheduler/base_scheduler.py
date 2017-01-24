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
