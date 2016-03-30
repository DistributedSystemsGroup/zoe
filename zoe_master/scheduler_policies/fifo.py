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

from zoe_master.stats import SchedulerStats
from zoe_master.scheduler_policies.base import BaseSchedulerPolicy
from zoe_master.state.application import ApplicationDescription
from zoe_master.state.execution import Execution
from zoe_master.config import singletons


class FIFOSchedulerPolicy(BaseSchedulerPolicy):
    def __init__(self, platform):
        super().__init__(platform)
        self.waiting_list = []
        self.starting_list = []

    def admission_control(self, app: ApplicationDescription) -> bool:
        swarm_stats = singletons['stats_manager'].swarm_stats
        if app.total_memory() < swarm_stats.memory_total:
            return True
        else:
            return False

    def execution_submission(self, execution: Execution):
        self.waiting_list.append(execution)

    def execution_kill(self, execution):
        try:
            self.waiting_list.remove(execution)
        except ValueError:
            pass

        try:
            self.starting_list.remove(execution)
        except ValueError:
            pass

    def runnable_get(self) -> Execution:
        if len(self.waiting_list) == 0:
            return None

        mem_reserved = sum([node.memory_reserved for node in singletons['stats_manager'].swarm_stats.nodes])
        mem_available = singletons['stats_manager'].swarm_stats.memory_total - mem_reserved
        candidate = self.waiting_list[0]
        if mem_available >= candidate.application.total_memory():
            self.waiting_list.pop(0)
            self.starting_list.append(candidate)
            return candidate
        else:
            return None

    def start_successful(self, execution: Execution) -> None:
        self.starting_list.remove(execution)

    def start_failed(self, execution: Execution) -> None:
        self.starting_list.remove(execution)
        self.waiting_list.append(execution)  # append or insert(0, ...) ?

    def stats(self):
        ret = SchedulerStats()
        ret.count_waiting = len(self.waiting_list)
        ret.waiting_list = []
        for e in self.waiting_list:
            ret.waiting_list.append(e.name)
        ret.timestamp = time.time()
        return ret
