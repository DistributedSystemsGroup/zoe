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

import time

from flask_restful import Resource, request

from zoe_lib.version import ZOE_API_VERSION, ZOE_APPLICATION_FORMAT_VERSION, ZOE_VERSION
from zoe_master.state.manager import StateManager
from zoe_master.platform_manager import PlatformManager
from zoe_master.rest_api.utils import catch_exceptions
from zoe_master.rest_api.auth.authentication import authenticate
from zoe_master.config import singletons, get_conf


class InfoAPI(Resource):
    """
    :type state: StateManager
    :type platform: PlatformManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']
        self.platform = kwargs['platform']

    @catch_exceptions
    def get(self):
        start_time = time.time()
        calling_user = authenticate(request, self.state)

        ret = {
            'version': ZOE_VERSION,
            'api_version': ZOE_API_VERSION,
            'application_format_version': ZOE_APPLICATION_FORMAT_VERSION,
            'name_prefix': get_conf().container_name_prefix
        }

        singletons['metric'].metric_api_call(start_time, 'info', '', calling_user)
        return ret
