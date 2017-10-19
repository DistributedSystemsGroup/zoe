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
import queue

from zoe_lib.config import get_conf

log = logging.getLogger(__name__)

METRIC_INTERVAL = 20


def time_diff_ms(start: float, end: float) -> int:
    """Return a time difference in milliseconds."""
    return int((end - start) * 1000)


class BaseMetricSender:
    """Base class for collecting and sending out metrics."""

    BUFFER_MAX_SIZE = 6

    def __init__(self, state):
        self.state = state
        self._queue = queue.Queue()
        self._buffer = []
        self._th = None
        self._th = threading.Thread(name='metrics', target=self._metrics_loop, daemon=True)
        self.deployment_name = get_conf().deployment_name

    def _start(self):
        self._th.start()

    def metric_api_call(self, time_start, action):
        """Compute and pass the metric point of an API call to the sender thread."""
        time_end = time.time()
        diff = time_diff_ms(time_start, time_end)
        point = "api latency: {} took {} ms".format(action, diff)
        self._queue.put(point)

    def _send_buffer(self):
        """
        Sends the buffered data.

        Needs to be redefined in child classes to support other metrics databases. Is called in thread context.
        """
        raise NotImplementedError

    def quit(self):
        """Terminates the sender thread."""
        self._queue.put("quit")
        self._th.join()

    def _metrics_loop(self):
        stop = False
        while not stop:
            time_start = time.time()
            while not self._queue.empty():
                data = self._queue.get(block=False)
                if data == 'quit':
                    stop = True
                else:
                    self._buffer.append(data)
            self._send_buffer()

            sleep_time = METRIC_INTERVAL - (time.time() - time_start)
            if sleep_time > 0 and not stop:
                time.sleep(sleep_time)
