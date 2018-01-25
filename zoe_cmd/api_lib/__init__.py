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
"""
This package contains the Zoe library, with modules used by more than one of the Zoe components. This library can also be used to write new clients for Zoe.
"""

import requests

from zoe_lib.version import ZOE_VERSION, ZOE_API_VERSION
from zoe_lib.exceptions import ZoeAPIException
from .info import ZoeInfoAPI
from .validation import ZoeValidationAPI
from .executions import ZoeExecutionsAPI
from .services import ZoeServiceAPI
from .statistics import ZoeStatisticsAPI


class ZoeAPI:
    """The main class to use the Zoe REST API client-side."""
    def __init__(self, url, user, password):
        self.url = url
        self.token, self.auth_user = self._login(user, password)
        self.info = ZoeInfoAPI(url, self.token)
        self.validation = ZoeValidationAPI(url, self.token)
        self.executions = ZoeExecutionsAPI(url, self.token)
        self.services = ZoeServiceAPI(url, self.token)
        self.statistics = ZoeStatisticsAPI(url, self.token)
        self._check_api_version()

    def _check_api_version(self):
        """Checks if there is a version mismatch between server and client."""
        try:
            self.info.info()
            return True
        except ZoeAPIException:
            print('Error: this client can talk to ZOE v. {}, but server is reporting an error'.format(ZOE_VERSION,))
            print('Error: your client is too old (or too new) to speak with the configured server')
            print('Error: check the version this server is running at the bottom of this web page: {}'.format(self.info.url))
            return False

    def _login(self, user, password):
        url = self.url + '/api/' + ZOE_API_VERSION + '/login'
        try:
            req = requests.get(url, auth=(user, password))
        except requests.exceptions.Timeout:
            raise ZoeAPIException('HTTP connection timeout')
        except requests.exceptions.HTTPError:
            raise ZoeAPIException('Invalid HTTP response')
        except requests.exceptions.ConnectionError as e:
            raise ZoeAPIException('Connection error: {}'.format(e))

        return req.headers['Set-Cookie'], req.json()['user']
