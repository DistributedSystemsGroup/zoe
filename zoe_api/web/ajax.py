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

"""Ajax API for the Zoe web interface."""

import datetime
import json

from tornado.escape import json_decode

from zoe_lib.config import get_conf
import zoe_api.exceptions
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.utils import catch_exceptions
from zoe_api.web.custom_request_handler import ZoeRequestHandler


class AjaxEndpointWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def post(self):
        """AJAX POST requests."""
        uid, role = get_auth(self)

        request = json_decode(self.request.body)

        if request['type'] == 'start':
            app_descr = json.load(open('contrib/zoeapps/eurecom_aml_lab.json', 'r'))
            execution = self.api_endpoint.execution_list(uid, role, name='aml-lab')
            if len(execution) == 0:
                exec_id = self.api_endpoint.execution_start(uid, role, 'aml-lab', app_descr)
            else:
                execution = execution[0]
                exec_id = execution.id
            response = {
                'status': 'ok',
                'execution_id': exec_id
            }
        elif request['type'] == 'query_status':
            try:
                execution = self.api_endpoint.execution_by_id(uid, role, request['exec_id'])
            except zoe_api.exceptions.ZoeNotFoundException:
                response = {
                    'status': 'ok',
                    'exec_status': 'none'
                }
            else:
                response = {
                    'status': 'ok',
                    'exec_status': execution.status
                }
                if execution.status == execution.RUNNING_STATUS:
                    response['ttl'] = ((execution.time_start + datetime.timedelta(hours=get_conf().aml_ttl)) - datetime.datetime.now()).total_seconds()
                    services_info_, endpoints = self.api_endpoint.execution_endpoints(uid, role, execution)
                    response['endpoints'] = endpoints
                elif execution.status == execution.ERROR_STATUS or execution.status == execution.TERMINATED_STATUS:
                    self.api_endpoint.execution_delete(uid, role, execution.id)
        else:
            response = {
                'status': 'error',
                'message': 'unknown request type'
            }

        self.write(response)
