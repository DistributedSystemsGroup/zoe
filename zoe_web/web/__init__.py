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
import zoe_web.web.start
import zoe_web.web.executions

from zoe_lib.version import ZOE_API_VERSION, ZOE_VERSION


def web_init() -> Blueprint:
    web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

    web_bp.context_processor(inject_version)

    web_bp.add_url_rule('/', 'index', zoe_web.web.start.index)
    web_bp.add_url_rule('/user', 'home_user', zoe_web.web.start.home_user)

    web_bp.add_url_rule('/executions/new', 'execution_define', zoe_web.web.executions.execution_define)
    web_bp.add_url_rule('/executions/start', 'execution_start', zoe_web.web.executions.execution_start, methods=['POST'])
    web_bp.add_url_rule('/executions/restart/<int:execution_id>', 'execution_restart', zoe_web.web.executions.execution_restart)
    web_bp.add_url_rule('/executions/terminate/<int:execution_id>', 'execution_terminate', zoe_web.web.executions.execution_terminate)
    web_bp.add_url_rule('/executions/inspect/<int:execution_id>', 'execution_inspect', zoe_web.web.executions.execution_inspect)

    return web_bp


def inject_version():
    return {
        'zoe_version': ZOE_VERSION,
        'zoe_api_version': ZOE_API_VERSION,
    }
