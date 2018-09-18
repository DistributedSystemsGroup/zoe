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
import zoe_api.web.admin

import zoe_lib.config
from zoe_lib.version import ZOE_API_VERSION, ZOE_VERSION


def web_init(api_endpoint) -> List[tornado.web.URLSpec]:
    """Tornado init for the web interface."""

    route_args = {
        'api_endpoint': api_endpoint
    }
    base_path = zoe_lib.config.get_conf().reverse_proxy_path
    web_routes = [
        tornado.web.url(base_path + r'/', zoe_api.web.start.RootWeb, route_args, name='root'),
        tornado.web.url(base_path + r'/user', zoe_api.web.start.HomeWeb, route_args, name='home_user'),
        tornado.web.url(base_path + r'/login', zoe_api.web.start.LoginWeb, route_args, name='login'),
        tornado.web.url(base_path + r'/logout', zoe_api.web.start.LogoutWeb, route_args, name='logout'),

        tornado.web.url(base_path + r'/executions', zoe_api.web.executions.ExecutionListWeb, route_args, name='execution_list'),
        tornado.web.url(base_path + r'/executions/([0-9]+)', zoe_api.web.executions.ExecutionListWeb, route_args, name='execution_list_page'),
        tornado.web.url(base_path + r'/executions/start', zoe_api.web.executions.ExecutionStartWeb, route_args, name='execution_start'),
        tornado.web.url(base_path + r'/executions/restart/([0-9]+)', zoe_api.web.executions.ExecutionRestartWeb, route_args, name='execution_restart'),
        tornado.web.url(base_path + r'/executions/terminate/([0-9]+)', zoe_api.web.executions.ExecutionTerminateWeb, route_args, name='execution_terminate'),
        tornado.web.url(base_path + r'/executions/inspect/([0-9]+)', zoe_api.web.executions.ExecutionInspectWeb, route_args, name='execution_inspect'),
        tornado.web.url(base_path + r'/service/logs/([0-9]+)', zoe_api.web.executions.ServiceLogsWeb, route_args, name='service_logs'),

        tornado.web.url(base_path + r'/websocket', zoe_api.web.websockets.WebSocketEndpointWeb, route_args, name='websocket'),

        tornado.web.url(base_path + r'/zapp-shop', zoe_api.web.zapp_shop.ZAppShopHomeWeb, route_args, name='zappshop'),
        tornado.web.url(base_path + r'/zapp-shop/logo/([0-9a-z_\-.]+)', zoe_api.web.zapp_shop.ZAppLogoWeb, route_args, name='zappshop_logo'),
        tornado.web.url(base_path + r'/zapp-shop/start/([0-9a-z_\-.]+)', zoe_api.web.zapp_shop.ZAppStartWeb, route_args, name='zappshop_start'),

        tornado.web.url(base_path + r'/status', zoe_api.web.status.StatusEndpointWeb, route_args, name='status'),

        tornado.web.url(base_path + r'/admin/users', zoe_api.web.admin.UsersEndpointWeb, route_args, name='admin_users'),
        tornado.web.url(base_path + r'/admin/roles', zoe_api.web.admin.RolesEndpointWeb, route_args, name='admin_roles'),
        tornado.web.url(base_path + r'/admin/quotas', zoe_api.web.admin.QuotasEndpointWeb, route_args, name='admin_quotas')
    ]

    return web_routes


def inject_version():
    """Inject some template variables in all templates."""
    return {
        'zoe_version': ZOE_VERSION,
        'zoe_api_version': ZOE_API_VERSION,
    }
