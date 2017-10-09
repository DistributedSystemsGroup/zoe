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

from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.utils import get_auth, catch_exceptions
from zoe_api.web.custom_request_handler import ZoeRequestHandler
from zoe_api.exceptions import ZoeException


class StatusEndpointWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self):
        """Status and statistics page."""
        uid, role = get_auth(self)
        if uid is None or role != 'admin':
            return self.redirect(self.get_argument('next', u'/login'))

        stats = self.api_endpoint.statistics_scheduler(uid, role)
        if stats is None:
            raise ZoeException('Cannot retrieve statistics from the Zoe master')

        executions_in_queue = {}
        for exec_id in stats['queue']:
            executions_in_queue[exec_id] = self.api_endpoint.execution_by_id(uid, role, exec_id)
        for exec_id in stats['running_queue']:
            executions_in_queue[exec_id] = self.api_endpoint.execution_by_id(uid, role, exec_id)

        max_service_count = max([len(node['services']) for node in stats['platform_stats']['nodes']])

        template_vars = {
            "uid": uid,
            "role": role,
            "stats": stats,
            "executions_in_queue": executions_in_queue,
            "max_service_count": max_service_count
        }

        self.render('status.html', **template_vars)
