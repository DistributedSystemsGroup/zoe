# Copyright (c) 2018, Daniele Venzano
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

"""Request handler for the Zoe API."""

import logging

from zoe_api.custom_request_handler import ZoeRequestHandler
from zoe_api.exceptions import ZoeAuthException

log = logging.getLogger(__name__)


class ZoeAPIRequestHandler(ZoeRequestHandler):
    """RequestHandler class for Zoe Web interface."""

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        self._manage_cors_headers()

    def _manage_cors_headers(self):
        """Set up the headers for enabling CORS."""
        if self.request.headers.get('Origin') is None:
            self.set_header("Access-Control-Allow-Origin", "*")
        else:
            self.set_header("Access-Control-Allow-Origin", self.request.headers.get('Origin'))
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type, origin, authorization, accept, client-security-token")
        self.set_header("Access-Control-Allow-Methods", "OPTIONS, GET, DELETE")
        self.set_header("Access-Control-Max-Age", "1000")

    def options(self):
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    def get_current_user(self):
        """In case auth fails, redirect to login page."""
        try:
            user = super().get_current_user()
        except ZoeAuthException as e:
            self.set_status(401, "Unauthorized access: {}".format(e))
            return None
        return user
