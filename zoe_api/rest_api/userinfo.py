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

"""The Info API endpoint."""

from tornado.web import RequestHandler
from zoe_api.rest_api.utils import get_auth, catch_exceptions


class UserInfoAPI(RequestHandler):
    """The UserInfo API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        if self.request.headers.get is None:
            self.set_header("Access-Control-Allow-Origin", "*")
        else:
            self.set_header("Access-Control-Allow-Origin", self.request.headers.get('Origin'))
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type, origin, authorization, accept, client-security-token")
        self.set_header("Access-Control-Allow-Methods", "OPTIONS, GET, DELETE")
        self.set_header("Access-Control-Max-Age", "1000")
    
    @catch_exceptions    
    def options(self):
        """Needed for CORS."""
        self.set_status(204)
        self.finish()
        
    @catch_exceptions
    def get(self):
        """HTTP GET method."""
        uid, role = get_auth(self)

        ret = {
            'uid': uid,
            'role': role
        }

        self.write(ret)

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
