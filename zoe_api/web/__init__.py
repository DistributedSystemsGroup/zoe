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

"""Flask initialization for the web interface."""

from typing import List

import tornado.web

import zoe_api.web.start
import zoe_api.web.executions


def web_init() -> List[tornado.web.URLSpec]:
    """Tornado init for the web interface."""
    web_routes = [
        tornado.web.url(r'/', zoe_api.web.start.RootWeb, name='root'),
        tornado.web.url(r'/user', zoe_api.web.start.HomeWeb, name='home_user'),
        tornado.web.url(r'/login', zoe_api.web.start.LoginWeb, name='login'),

        tornado.web.url(r'/executions/new', zoe_api.web.executions.ExecutionDefineWeb, name='execution_define'),
        tornado.web.url(r'/executions/start', zoe_api.web.executions.ExecutionStartWeb, name='execution_start'),
        tornado.web.url(r'/executions/restart/([0-9]+)', zoe_api.web.executions.ExecutionRestartWeb, name='execution_restart'),
        tornado.web.url(r'/executions/terminate/([0-9]+)', zoe_api.web.executions.ExecutionTerminateWeb, name='execution_terminate'),
        tornado.web.url(r'/executions/delete/([0-9]+)', zoe_api.web.executions.ExecutionDeleteWeb, name='execution_delete'),
        tornado.web.url(r'/executions/inspect/([0-9]+)', zoe_api.web.executions.ExecutionInspectWeb, name='execution_inspect')
    ]

    return web_routes
