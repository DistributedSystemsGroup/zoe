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

"""The Service API endpoint."""

import logging

from flask_restful import Resource, request
from flask import Response

from zoe_api.rest_api.utils import catch_exceptions, get_auth
import zoe_api.api_endpoint

log = logging.getLogger(__name__)


class ServiceAPI(Resource):
    """The Service API endpoint."""
    def __init__(self, api_endpoint: zoe_api.api_endpoint.APIEndpoint) -> None:
        self.api_endpoint = api_endpoint

    @catch_exceptions
    def get(self, service_id) -> dict:
        """HTTP GET method."""
        uid, role = get_auth(request)

        service = self.api_endpoint.service_by_id(uid, role, service_id)

        return service.serialize()


class ServiceLogsAPI(Resource):
    """The Service logs API endpoint."""
    def __init__(self, api_endpoint: zoe_api.api_endpoint.APIEndpoint) -> None:
        self.api_endpoint = api_endpoint

    @catch_exceptions
    def get(self, service_id) -> dict:
        """HTTP GET method."""
        uid, role = get_auth(request)

        log_gen = self.api_endpoint.service_logs(uid, role, service_id, stream=True)

        def flask_stream():
            """Helper function to stream log data."""
            for log_line in log_gen:
                print(log_line)
                yield log_line.decode('utf-8')

        return Response(flask_stream(), mimetype='text/plain')
