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

"""The Discovery API endpoint."""

from zoe_api.rest_api.utils import catch_exceptions
from zoe_api.rest_api.custom_request_handler import BaseRequestHandler


class DiscoveryAPI(BaseRequestHandler):
    """The Discovery API endpoint."""

    @catch_exceptions
    def get(self, execution_id: int, service_group: str):
        """HTTP GET method."""
        self.api_endpoint.execution_by_id(0, 'admin', execution_id)
        if service_group != 'all':
            services = self.api_endpoint.service_list(0, 'admin', service_group=service_group, execution_id=execution_id)
        else:
            services = self.api_endpoint.service_list(0, 'admin', execution_id=execution_id)
        ret = {
            'service_type': service_group,
            'execution_id': execution_id,
            'dns_names': [s.dns_name for s in services]
        }

        self.write(ret)
