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

import time
import logging
import threading
import queue

log = logging.getLogger(__name__)


class BaseMetricSender(threading.Thread):
    def __init__(self, name, conf):
        super().__init__(name=name)

        self._deployment = conf.deployment_name
        self._queue = queue.Queue()

    def quit(self):
        pass

    def _time_diff_ms(self, start: float, end: float) -> int:
        return (end - start) * 1000

    def metric_api_call(self, time_start, api_name, action, calling_user):
        time_end = time.time()
        td = self._time_diff_ms(time_start, time_end)
        log.debug("api latency: {} {} user {} took {} ms".format(api_name, action, calling_user.name, td))

    def run(self):
        pass
