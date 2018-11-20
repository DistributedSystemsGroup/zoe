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

"""Main points of entry for the Zoe web interface."""

from zoe_api.web.request_handler import ZoeWebRequestHandler
from zoe_api.exceptions import ZoeException
from zoe_lib.config import get_conf


class StatusEndpointWeb(ZoeWebRequestHandler):
    """Handler class"""

    def _calculate_load(self, sched):
        core_total = sched['platform_stats']['cores_total']
        memory_total = sched['platform_stats']['memory_total']
        core_reserved = 0
        memory_reserved = 0
        for node in sched['platform_stats']['nodes']:
            core_reserved += node['cores_reserved']
            memory_reserved += node['memory_reserved']
        core_usage = core_reserved / core_total
        memory_usage = memory_reserved / memory_total
        return core_usage, memory_usage

    def get(self):
        """Status and statistics page."""
        if self.current_user is None or not self.current_user.role.can_see_status:
            return

        stats = self.api_endpoint.statistics_scheduler()
        if stats is None:
            raise ZoeException('Cannot retrieve statistics from the Zoe master')

        executions_in_queue = {}
        for exec_id in stats['queue']:
            executions_in_queue[exec_id] = self.api_endpoint.execution_by_id(None, exec_id)
        for exec_id in stats['running_queue']:
            executions_in_queue[exec_id] = self.api_endpoint.execution_by_id(None, exec_id)
        for exec_id in stats['termination_queue']:
            executions_in_queue[exec_id] = self.api_endpoint.execution_by_id(None, exec_id)

        services_per_node = {}
        for node in stats['platform_stats']['nodes']:
            services_per_node[node['name']] = self.api_endpoint.sql.services.select(backend_host=node['name'], backend_status='started')
            for service in services_per_node[node['name']]:
                if service.id not in node['service_stats']:
                    node['service_stats'][service.id] = {
                        'mem_limit': 0,
                        'core_limit': 0
                    }

        max_service_count = max([len(services_per_node[name]) for name in services_per_node])

        template_vars = {
            "stats": stats,
            "executions_in_queue": executions_in_queue,
            "services_per_node": services_per_node,
            "max_service_count": max_service_count,
            'eurecom': get_conf().eurecom,
            'platform_load': self._calculate_load()
        }

        self.render('status.jinja2', **template_vars)
