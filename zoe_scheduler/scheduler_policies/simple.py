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

from zoe_scheduler.platform_status import PlatformStatus
from zoe_scheduler.stats import SchedulerStats
from zoe_scheduler.scheduler_policies.base import BaseSchedulerPolicy
from common.application_description import ZoeApplication


class SimpleSchedulerPolicy(BaseSchedulerPolicy):
    def __init__(self, platform_status: PlatformStatus):
        self.platform_status = platform_status
        self.waiting_list = []
        self.running_list = []

    def admission_control(self, app_description: ZoeApplication) -> bool:
        if app_description.total_memory() < self.platform_status.swarm_status.memory_total:
            return True
        else:
            return False

    def execution_submission(self, execution_id: int, app_description: ZoeApplication):
        self.waiting_list.append((execution_id, app_description))

    def execution_kill(self, execution_id):
        for e in self.waiting_list:
            if e[0] == execution_id:
                self.waiting_list.remove(e)
                return
        for e in self.running_list:
            if e[0] == execution_id:
                self.running_list.remove(e)
                return

    def runnable_get(self) -> (int, ZoeApplication):
        try:
            exec_id, resources = self.waiting_list.pop(0)
        except IndexError:
            return None, None

        return exec_id, resources

    def stats(self):
        ret = SchedulerStats()
        ret.count_waiting = len(self.waiting_list)
        ret.timestamp = time.time()
        return ret
