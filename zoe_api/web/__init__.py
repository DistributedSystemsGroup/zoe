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
import zoe_api.web.websockets
import zoe_api.web.executions
import zoe_api.web.zapp_shop
import zoe_api.web.status

from zoe_api.web.filemanager import FileListHandler, UploadHandler, MainWsHandler, DownloadHandler

from zoe_lib.version import ZOE_API_VERSION, ZOE_VERSION


def web_init(api_endpoint) -> List[tornado.web.URLSpec]:
    """Tornado init for the web interface."""

    route_args = {
        'api_endpoint': api_endpoint
    }
    web_routes = [
        tornado.web.url(r'/', zoe_api.web.start.RootWeb, route_args, name='root'),
        tornado.web.url(r'/user', zoe_api.web.start.HomeWeb, route_args, name='home_user'),
        tornado.web.url(r'/login', zoe_api.web.start.LoginWeb, route_args, name='login'),
        tornado.web.url(r'/logout', zoe_api.web.start.LogoutWeb, route_args, name='logout'),

        tornado.web.url(r'/executions', zoe_api.web.executions.ExecutionListWeb, route_args, name='execution_list'),
        tornado.web.url(r'/executions/start', zoe_api.web.executions.ExecutionStartWeb, route_args, name='execution_start'),
        tornado.web.url(r'/executions/restart/([0-9]+)', zoe_api.web.executions.ExecutionRestartWeb, route_args, name='execution_restart'),
        tornado.web.url(r'/executions/terminate/([0-9]+)', zoe_api.web.executions.ExecutionTerminateWeb, route_args, name='execution_terminate'),
        tornado.web.url(r'/executions/inspect/([0-9]+)', zoe_api.web.executions.ExecutionInspectWeb, route_args, name='execution_inspect'),
        tornado.web.url(r'/service/logs/([0-9]+)', zoe_api.web.executions.ServiceLogsWeb, route_args, name='service_logs'),

        tornado.web.url(r'/websocket', zoe_api.web.websockets.WebSocketEndpointWeb, route_args, name='websocket'),

        tornado.web.url(r'/zapp-shop', zoe_api.web.zapp_shop.ZAppShopHomeWeb, route_args, name='zappshop'),
        tornado.web.url(r'/zapp-shop/logo/([a-z\-.]+)', zoe_api.web.zapp_shop.ZAppLogoWeb, route_args, name='zappshop_logo'),
        tornado.web.url(r'/zapp-shop/start/([0-9a-z\-.]+)', zoe_api.web.zapp_shop.ZAppStartWeb, route_args, name='zappshop_start'),

        tornado.web.url(r'/status', zoe_api.web.status.StatusEndpointWeb, route_args, name='status'),

        tornado.web.url(r"/ws/", FileListHandler, name='filemanager'),
        tornado.web.url(r"/ws/upload", UploadHandler, route_args),
        tornado.web.url(r"/ws/ws", MainWsHandler, route_args),
        tornado.web.url(r"/ws/download/(.*)", DownloadHandler, route_args)
    ]

    return web_routes


def inject_version():
    """Inject some template variables in all templates."""
    return {
        'zoe_version': ZOE_VERSION,
        'zoe_api_version': ZOE_API_VERSION,
    }
