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

"""The high-level interface that Zoe uses to talk to the configured container backend."""

from zoe_lib.state import Service, Execution

JUPYTER_NOTEBOOK = 'BASE_URL'
MONGO_EXPRESS = 'ME_CONFIG_SITE_BASEURL'

JUPYTER_PORT = '8888'
MONGO_PORT = '27017'

def gen_proxypath(execution: Execution, service: Service):
    """ gen proxy address path """
    proxy_path_value = '/zoe/' + execution.user_id + '/' + str(execution.id) + '/' + service.name
    return proxy_path_value
