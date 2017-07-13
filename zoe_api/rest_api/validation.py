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

"""The Info API endpoint."""

import tornado.escape

from zoe_api.rest_api.utils import catch_exceptions
import zoe_api.exceptions
from zoe_api.rest_api.custom_request_handler import BaseRequestHandler


class ZAppValidateAPI(BaseRequestHandler):
    """The Info API endpoint."""

    @catch_exceptions
    def post(self):
        """HTTP GET method."""
        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        application_description = data['application']

        self.api_endpoint.zapp_validate(application_description)

        self.write({'validation': 'ok'})
