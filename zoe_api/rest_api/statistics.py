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

"""The Scheduler Statistics API endpoint."""

from zoe_api.rest_api.utils import catch_exceptions
from zoe_api.rest_api.custom_request_handler import BaseRequestHandler


class SchedulerStatsAPI(BaseRequestHandler):
    """The Scheduler Statistics API endpoint."""

    @catch_exceptions
    def get(self):
        """HTTP GET method."""
        statistics = self.api_endpoint.statistics_scheduler(0, 'guest')
        self.write(statistics)
