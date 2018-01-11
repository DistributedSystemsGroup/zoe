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

"""Base class for metrics."""

import time
import logging
import threading
from copy import deepcopy

from zoe_lib.config import get_conf
from zoe_master.backends.interface import get_platform_state
from zoe_master.metrics.kairosdb import KairosDBInMetrics

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
        self._current_platform_stats = None
        if get_conf().kairosdb_enable:
            self.usage_metrics = KairosDBInMetrics()
        else:
            self.usage_metrics = None

    def quit(self):
        """Terminates the sender thread."""
        self.stop.set()
        self.join()

    def run(self):
        """Wraps the loop to catch exceptions"""
        while True:
            try:
                self._real_run()
            except BaseException:  # pylint: disable=broad-except
                log.exception("Exception in metrics thread")
            else:
                log.info('Metrics thread terminated')
                break

    def _real_run(self):
        """The thread loop."""
        while True:
            time_start = time.time()

            self._current_platform_stats = get_platform_state()
            if self.usage_metrics is not None:
                for node in self._current_platform_stats.nodes:
                    node_cores = 0
                    node_memory = 0
                    for service_id in node.service_stats:
                        usage = self.usage_metrics.get_service_usage(service_id)
                        try:
                            node.service_stats[service_id]['cores_in_use'] = usage['cpu_usage']
                            node.service_stats[service_id]['memory_in_use'] = usage['mem_usage']
                        except KeyError:  # happens while a service is being terminated
                            continue
                        except TypeError:  # happens while KairosDB cannot be reached
                            continue
                        node_cores += usage['cpu_usage']
                        node_memory += usage['mem_usage']

                    node.cores_in_use = node_cores
                    node.memory_in_use = node_memory

            sleep_time = METRIC_INTERVAL - (time.time() - time_start)
            if sleep_time > 0 and self.stop.wait(timeout=sleep_time):
                break

    @property
    def current_stats(self):
        """Returns a snapshot of the current metrics."""
        return deepcopy(self._current_platform_stats)
