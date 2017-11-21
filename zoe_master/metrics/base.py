# Copyright (c) 2016, Daniele Venzano
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

"""Base class for metrics."""

import time
import logging
import threading

from zoe_lib.config import get_conf
from zoe_master.backends.interface import get_platform_state

log = logging.getLogger(__name__)

METRIC_INTERVAL = 20


def time_diff_ms(start: float, end: float) -> int:
    """Return a time difference in milliseconds."""
    return int((end - start) * 1000)


class StatsManager(threading.Thread):
    """Class for collecting and sending out metrics and statistics."""

    def __init__(self, state):
        super().__init__(name='metrics', daemon=True)
        self.state = state
        self.deployment_name = get_conf().deployment_name
        self.stop = threading.Event()
        self.current_platform_stats = None

    def quit(self):
        """Terminates the sender thread."""
        self.stop.set()
        self.join()

    def run(self):
        """The thread loop."""
        while True:
            time_start = time.time()

            self.current_platform_stats = get_platform_state()

            sleep_time = METRIC_INTERVAL - (time.time() - time_start)
            if sleep_time > 0 and self.stop.wait(timeout=sleep_time):
                break
