# Copyright (c) 2015, Daniele Venzano
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

from flask import Blueprint

web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

import zoe_web.web.start
import zoe_web.web.status
import zoe_web.web.executions

from zoe_lib.version import ZOE_API_VERSION, ZOE_VERSION


@web_bp.context_processor
def inject_version():
    return {
        'zoe_version': ZOE_VERSION,
        'zoe_api_version': ZOE_API_VERSION,
    }
