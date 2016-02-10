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

import time

from zoe_scheduler.stats import SchedulerStats
from zoe_scheduler.scheduler_policies.base import BaseSchedulerPolicy
from zoe_scheduler.state.application import Application
from zoe_scheduler.state.execution import Execution


class FIFOSchedulerPolicy(BaseSchedulerPolicy):
    def __init__(self, platform):
        super().__init__(platform)
        self.waiting_list = []
        self.running_list = []

    def admission_control(self, app: Application) -> bool:
        swarm_stats = self.platform.swarm_stats()
        if app.total_memory() < swarm_stats.memory_total:
            return True
        else:
            return False

    def execution_submission(self, execution: Execution):
        self.waiting_list.append(execution)

    def execution_kill(self, execution):
        for e in self.waiting_list:
            if e == execution:
                self.waiting_list.remove(e)
                return
        for e in self.running_list:
            if e[0] == execution:
                self.running_list.remove(e)
                return

    def runnable_get(self) -> Execution:
        try:
            execution = self.waiting_list.pop(0)
        except IndexError:
            return None

        return execution

    def stats(self):
        ret = SchedulerStats()
        ret.count_waiting = len(self.waiting_list)
        ret.timestamp = time.time()
        return ret
