# Copyright (c) 2016, Quang-Nhat Hoang-Xuan
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

"""Base authenticator class."""

import docker
import time
import logging

import zoe_api.proxy.base
import zoe_api.api_endpoint
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)

class NginxProxy(zoe_api.proxy.base.BaseProxy):
    """Nginx proxy class."""
    def __init__(self, apiEndpoint):
        return {}

    def proxify(self, uid, role, id):
        return {}

    def unproxify(self, uid, role, id):
        return {}
