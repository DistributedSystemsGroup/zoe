# Copyright (c) 2018, Daniele Venzano
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

"""Retrieves metrics about services from InfluxDB."""

import logging

import requests

from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class InfluxDBInMetrics:
    """InfluxDB metrics."""
    def __init__(self):
        self.base_url = get_conf().influxdb_url

    def get_service_usage(self, service_id):
        """Query the DB for the current usage metrics."""
        query_cpu = 'SELECT mean("usage_percent") FROM "docker_container_cpu" WHERE "zoe_service_id" = \'{}\' AND time >= now() - 3m GROUP BY time(2m) ORDER BY time DESC LIMIT 1'.format(service_id)
        query_mem = 'SELECT mean("usage") FROM "docker_container_mem" WHERE "zoe_service_id" = \'{}\' AND time >= now() - 3m GROUP BY time(2m) ORDER BY time DESC LIMIT 1'.format(service_id)

        url = self.base_url + '/query'
        resp = requests.post(url, data={"db": 'telegraf', 'q': query_cpu + ';' + query_mem})
        influx_resp = resp.json()
        if "error" in influx_resp:
            log.warning("InfluxDB reported an error: {}".format(influx_resp['error']))
            return None
        return self._extract_data(influx_resp)

    def _extract_data(self, data):
        ret = {}
        cpu_results = data['results'][0]
        assert cpu_results['statement_id'] == 0
        if 'series' in cpu_results:
            val = cpu_results['series'][0]['values'][0][1]
            if val is None:
                ret['cpu_usage'] = 0
            else:
                ret['cpu_usage'] = val
        else:
            ret['cpu_usage'] = 0

        mem_results = data['results'][1]
        assert mem_results['statement_id'] == 1
        if 'series' in mem_results:
            val = mem_results['series'][0]['values'][0][1]
            if val is None:
                ret['mem_usage'] = 0
            else:
                ret['mem_usage'] = val
        else:
            ret['mem_usage'] = 0
        return ret
