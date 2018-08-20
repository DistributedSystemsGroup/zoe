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

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler
from zoe_api.exceptions import ZoeException


class DiscoveryAPI(ZoeAPIRequestHandler):
    """The Discovery API endpoint."""

    def get(self, execution_id: int, service_group: str):
        """HTTP GET method."""
        if self.current_user is None:
            return

        try:
            self.api_endpoint.execution_by_id(self.current_user, execution_id)
            if service_group != 'all':
                services = self.api_endpoint.service_list(self.current_user, service_group=service_group, execution_id=execution_id)
            else:
                services = self.api_endpoint.service_list(self.current_user, execution_id=execution_id)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        ret = {
            'service_type': service_group,
            'execution_id': execution_id,
            'dns_names': [s.dns_name for s in services]
        }

        self.write(ret)
