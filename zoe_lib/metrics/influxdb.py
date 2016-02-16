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

log = logging.getLogger(__name__)

_buffer = []
_influxdb_endpoint = None


def init(influxdb_dbname, influxdb_url):
    global _influxdb_endpoint
    _influxdb_endpoint = influxdb_url + '/write?precision=ms&db=' + influxdb_dbname


def _send_buffer(self):
    payload = '\n'.join(self.buffer)
    r = requests.post(self.influxdb_endpoint, data=payload)
    if r.status_code != 204:
        log.error('error writing metrics to influxdb')
    self.buffer = []


def point(conf, measurement_name, value, **kwargs):
    ts = time.time()
    point_str = measurement_name
    for k, v in kwargs.items():
        point_str += "," + k + '=' + v
    point_str += " value=" + str(value)
    point_str += " " + str(int(ts * 1000))

    _buffer.append(point_str)
    if len(_buffer) > 5:
        _send_buffer(conf)
