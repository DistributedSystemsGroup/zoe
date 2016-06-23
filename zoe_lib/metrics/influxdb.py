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
import requests
import logging
import queue

import zoe_lib.metrics.base

log = logging.getLogger(__name__)


class InfluxDBMetricSender(zoe_lib.metrics.base.BaseMetricSender):
    def __init__(self, conf):
        super().__init__('influxdb_sender', conf)

        self._buffer = []
        self._influxdb_endpoint = conf.influxdb_url + '/write?precision=ms&db=' + conf.influxdb_dbname
        self.retries = 5

    def _send_buffer(self):
        error = False
        if self._influxdb_endpoint is not None and len(self._buffer) > 0:
            payload = '\n'.join(self._buffer)
            try:
                r = requests.post(self._influxdb_endpoint, data=payload)
            except:
                log.exception('error writing metrics to influxdb, will retry {} times'.format(self.retries))
                error = True
            else:
                if r.status_code != 204:
                    log.error('error writing metrics to influxdb, will retry {} times'.format(self.retries))
                    error = True
        if error:
            if self.retries <= 0:
                self.retries = 5
                self._buffer.clear()
            else:
                self.retries -= 1
        else:
            self._buffer.clear()

    def quit(self):
        self._queue.put('quit')

    def point(self, measurement_name: str, value: int, **kwargs):
        ts = time.time()
        point_str = measurement_name
        for k, v in kwargs.items():
            point_str += "," + k + '=' + v
        point_str += ',' + 'deployment' + '=' + self._deployment
        point_str += " value=" + str(value)
        point_str += " " + str(int(ts * 1000))

        self._queue.put(point_str)

    def metric_api_call(self, time_start, action):
        time_end = time.time()
        td = self._time_diff_ms(time_start, time_end)
        self.point("api_latency", td, api_call=action)

    def run(self):
        log.info('starting influxdb metric sender thread')
        while True:
            try:
                data = self._queue.get(timeout=1)
            except queue.Empty:
                if len(self._buffer) > 0:
                    self._send_buffer()
                continue

            if data == 'quit':
                log.info('influxdb thread got a quit command')
                if len(self._buffer) > 0:
                    self._send_buffer()
                break

            if data != 'quit':
                self._buffer.append(data)
                if len(self._buffer) > 6:
                    self._send_buffer()
