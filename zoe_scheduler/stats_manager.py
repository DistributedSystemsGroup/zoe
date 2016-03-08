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

import threading
import time
import logging

from zoe_lib.swarm_client import SwarmClient
from zoe_scheduler.config import get_conf

log = logging.getLogger(__name__)


class StatsManager(threading.Thread):
    def __init__(self):
        super().__init__(name='stats', daemon=True)
        self.swarm = SwarmClient(get_conf())

        self._swarm_stats = None

    def run(self):
        log.info("Stats manager started")
        while True:
            try:
                self._swarm_stats = self.swarm.info()
            except:
                log.exception("Exception in stats thread")
            time.sleep(5)

    @property
    def swarm_stats(self):
        return self._swarm_stats
