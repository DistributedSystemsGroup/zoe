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

from zoe_scheduler.stats import PlatformStats
from zoe_scheduler.swarm_client import SwarmClient

log = logging.getLogger(__name__)


class PlatformStatus:
    def __init__(self, scheduler):
        self.swarm = SwarmClient()
        self.swarm_status = None
        self.scheduler = scheduler
        self.scheduler_status = None

    def update(self):
        self.swarm_status = self.swarm.info()
        self.scheduler_status = self.scheduler.scheduler_policy.stats()

    def stats(self):
        ret = PlatformStats()
        ret.scheduler = self.scheduler_status
        ret.swarm = self.swarm_status
        return ret
