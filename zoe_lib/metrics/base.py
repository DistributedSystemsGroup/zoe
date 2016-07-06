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

log = logging.getLogger(__name__)


def time_diff_ms(start: float, end: float) -> int:
    """Return a time difference in milliseconds."""
    return int((end - start) * 1000)


class BaseMetricSender:
    """Base class for collecting and sending out metrics."""

    BUFFER_MAX_SIZE = 6

    def __init__(self, deployment_name):
        self._queue = queue.Queue()
        self._buffer = []
        self._th = None
        self._th = threading.Thread(name='metrics', target=self._metrics_loop, daemon=True)
        self.deployment_name = deployment_name

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
        while True:
            try:
                data = self._queue.get(timeout=1)
            except queue.Empty:
                self._send_buffer()
                continue

            if data == 'quit':
                if len(self._buffer) > 0:
                    self._send_buffer()
                break

            if data != 'quit':
                self._buffer.append(data)
                if len(self._buffer) > self.BUFFER_MAX_SIZE:
                    self._send_buffer()
