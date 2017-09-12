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

"""Zoe App shop web pages."""

import logging

from zoe_api import zapp_shop
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.utils import get_auth, catch_exceptions
from zoe_api.web.custom_request_handler import ZoeRequestHandler

log = logging.getLogger(__name__)


class ZAppShopHomeWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self):
        """Home page with authentication."""
        uid, role = get_auth(self)
        if uid is None:
            return self.redirect(self.get_argument('next', u'/login'))

        zapps = zapp_shop.zshop_list_apps()

        template_vars = {
            "uid": uid,
            "role": role,
            'zapps': zapps,
        }
        self.render('zapp_shop.html', **template_vars)


class ZAppLogoWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, zapp_id):
        """Home page with authentication."""
        uid, role = get_auth(self)
        if uid is None:
            return self.redirect(self.get_argument('next', u'/login'))

        self.set_header("Content-type", "image/png")
        self.write(zapp_shop.get_logo(zapp_id))


class ZAppStartWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, zapp_id):
        """Home page with authentication."""
        uid, role = get_auth(self)
        if uid is None:
            return self.redirect(self.get_argument('next', u'/login'))

        manifest_index = int(zapp_id.split('-')[-1])
        zapp_id = "-".join(zapp_id.split('-')[:-1])
        zapps = zapp_shop.zshop_read_manifest(zapp_id)
        zapp = zapps[manifest_index]

        template_vars = {
            "uid": uid,
            "role": role,
            'zapp': zapp
        }
        self.render('zapp_start.html', **template_vars)

    @catch_exceptions
    def post(self, zapp_id):
        """Write the parameters in the description and start the ZApp."""
        uid, role = get_auth(self)
        if uid is None:
            return self.redirect(self.get_argument('next', u'/login'))

        manifest_index = int(zapp_id.split('-')[-1])
        zapp_id = "-".join(zapp_id.split('-')[:-1])
        zapps = zapp_shop.zshop_read_manifest(zapp_id)
        zapp = zapps[manifest_index]

        exec_name = self.get_argument('exec_name')

        app_descr = self._set_parameters(zapp.zoe_description, zapp.parameters)

        new_id = self.api_endpoint.execution_start(uid, role, exec_name, app_descr)

        self.redirect(self.reverse_url('execution_inspect', new_id))

    def _set_parameters(self, app_descr, params):
        for param in params:
            if param.kind == 'environment':
                for service in app_descr['services']:
                    for env in service['environment']:
                        if env[0] == param.name:
                            env[1] = self.get_argument(param.name)
            elif param.kind == 'command':
                for service in app_descr['services']:
                    if service['name'] == param.name:
                        service['command'] = self.get_argument(param.name)
                        break
            else:
                log.warning('Unknown parameter kind: {}, ignoring...'.format(param.kind))
        return app_descr
