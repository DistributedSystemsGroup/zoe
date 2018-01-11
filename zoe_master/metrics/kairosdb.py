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

"""Retrieves metrics about services from KairosDB."""

from datetime import datetime, timedelta
import logging

import requests

from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class KairosDBInMetrics:
    """KairosDB metrics."""
    def __init__(self):
        self.base_url = get_conf().kairosdb_url

        self.tags_url = self.base_url + '/api/v1/datapoints/query/tags'
        self.metrics_url = self.base_url + '/api/v1/datapoints/query'
        self.list_metrics_url = self.base_url + '/api/v1/metricnames'

    def _prepare_query(self):
        query = {
            'time_zone': 'UTC',
            'metrics': []
        }
        self._add_time_range(query)
        return query

    def _add_time_range(self, query, minutes_from_now=10):
        end = datetime.now()
        start = end - timedelta(minutes=minutes_from_now)
        query['start_absolute'] = int(start.timestamp() * 1000)
        query['end_absolute'] = int(end.timestamp() * 1000)

    def _add_metric(self, query, metric_name: str, tags, aggregators, limit: int):
        metric = {
            'name': metric_name,
        }
        if tags is not None:
            metric['tags'] = tags
        if aggregators is not None:
            metric['aggregators'] = aggregators
        if limit > 0:
            metric['limit'] = limit
        query['metrics'].append(metric)

    def get_service_usage(self, service_id):
        """Query the DB for the current usage metrics."""
        query = self._prepare_query()

        tags_cpu = {
            "field": ["usage_percent"],
            "zoe_service_id": service_id
        }
        aggregators_cpu = [
            {"name": "scale", "factor": "0.01"},
            {"name": "sum", "sampling": {"value": "1", "unit": "minutes"}, "align_sampling": False}
        ]
        self._add_metric(query, "docker_container_cpu", tags_cpu, aggregators_cpu, limit=0)

        tags_memory = {
            "field": ["usage"],
            "zoe_service_id": service_id
        }

        aggregators_memory = [
            {"name": "sum", "sampling": {"value": "1", "unit": "minutes"}, "align_sampling": False}
        ]
        self._add_metric(query, "docker_container_mem", tags_memory, aggregators_memory, limit=0)

        try:
            req = requests.post(self.metrics_url, json=query)
        except requests.exceptions.ConnectionError:
            return None
        return self._extract_data(req)

    def _extract_data(self, response):
        if response is None:
            return None
        if response.status_code != 200:
            error_msg = ''
            for error in response.json()['errors']:
                error_msg += ' {}'.format(error)
            log.error('kairosdb query error: {}'.format(error_msg))
            return None
        else:
            data = response.json()
            cpu_results = data['queries'][0]
            mem_results = data['queries'][1]

            if cpu_results['sample_size'] > 0:
                assert len(cpu_results['results']) == 1
                cpu_usage = cpu_results['results'][0]['values'][-1][1]
            else:
                cpu_usage = 0

            if mem_results['sample_size'] > 0:
                assert len(mem_results['results']) == 1
                mem_usage = mem_results['results'][0]['values'][-1][1]
            else:
                mem_usage = 0

            return {
                'cpu_usage': cpu_usage,
                'mem_usage': mem_usage
            }
