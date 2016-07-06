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

"""InfluxDB implementation of the metrics system."""

import time
import logging

import requests

import zoe_lib.metrics.base

log = logging.getLogger(__name__)


class InfluxDBMetricSender(zoe_lib.metrics.base.BaseMetricSender):
    """Sends metrics to InfluxDB."""

    RETRIES = 5

    def __init__(self, deployment_name, influxdb_url, influxdb_dbname):
        super().__init__(deployment_name)
        self._influxdb_endpoint = influxdb_url + '/write?precision=ms&db=' + influxdb_dbname
        self._retries = self.RETRIES
        self._start()

    def _send_buffer(self):
        error = False
        if self._influxdb_endpoint is not None and len(self._buffer) > 0:
            payload = '\n'.join(self._buffer)
            try:
                req = requests.post(self._influxdb_endpoint, data=payload)
            except Exception:
                log.exception('error writing metrics to influxdb, will retry {} times'.format(self._retries))
                error = True
            else:
                if req.status_code != 204:
                    log.error('error writing metrics to influxdb, will retry {} times'.format(self._retries))
                    error = True
        if error:
            if self._retries <= 0:
                self._retries = self.RETRIES
                self._buffer.clear()
            else:
                self._retries -= 1
        else:
            self._buffer.clear()

    def metric_api_call(self, time_start, action):
        """Compute and emit the run time of an API call."""
        time_end = time.time()
        diff = zoe_lib.metrics.base.time_diff_ms(time_start, time_end)

        point_str = "api_latency"
        point_str += ",api_call=" + action
        point_str += ',' + 'deployment' + '=' + self.deployment_name
        point_str += " value=" + str(diff)
        point_str += " " + str(int(time_end * 1000))

        self._queue.put(point_str)
