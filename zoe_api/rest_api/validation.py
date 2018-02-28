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

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler
from zoe_api.exceptions import ZoeException


class ZAppValidateAPI(ZoeAPIRequestHandler):
    """The Info API endpoint."""

    def post(self):
        """HTTP GET method."""
        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            self.set_status(400, 'Error decoding JSON data')
            return

        application_description = data['application']

        try:
            self.api_endpoint.zapp_validate(application_description)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.write({'validation': 'ok'})
