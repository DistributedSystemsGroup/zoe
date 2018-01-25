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

from tornado.web import MissingArgumentError

from zoe_api import zapp_shop
from zoe_api.web.request_handler import ZoeWebRequestHandler
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class ZAppShopHomeWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self):
        """Home page with authentication."""
        if self.current_user is None:
            return

        zapps = zapp_shop.zshop_list_apps(self.current_user.role)

        template_vars = {
            "user": self.current_user,
            'zapps': zapps,
        }
        self.render('zapp_shop.html', **template_vars)


class ZAppLogoWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self, zapp_id):
        """Home page with authentication."""
        if self.current_user is None:
            return

        self.set_header("Content-type", "image/png")

        manifest_index = int(zapp_id.split('-')[-1])
        zapp_id = "-".join(zapp_id.split('-')[:-1])
        zapps = zapp_shop.zshop_read_manifest(zapp_id)
        zapp = zapps[manifest_index]
        self.write(zapp_shop.get_logo(zapp))


class ZAppStartWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self, zapp_id):
        """Home page with authentication."""
        if self.current_user is None:
            return

        manifest_index = int(zapp_id.split('-')[-1])
        zapp_id = "-".join(zapp_id.split('-')[:-1])
        zapps = zapp_shop.zshop_read_manifest(zapp_id)
        zapp = zapps[manifest_index]

        template_vars = {
            "user": self.current_user,
            'zapp': zapp,
            'max_core_limit': get_conf().max_core_limit,
            'max_memory_limit': get_conf().max_memory_limit,
            'resources_are_customizable': self.current_user.role.can_customize_resources,
            'additional_volumes': get_conf().additional_volumes
        }
        self.render('zapp_start.html', **template_vars)

    def post(self, zapp_id):
        """Write the parameters in the description and start the ZApp."""
        if self.current_user is None:
            return

        manifest_index = int(zapp_id.split('-')[-1])
        zapp_id = "-".join(zapp_id.split('-')[:-1])
        zapps = zapp_shop.zshop_read_manifest(zapp_id)
        zapp = zapps[manifest_index]

        exec_name = self.get_argument('exec_name')

        app_descr = self._set_parameters(zapp.zoe_description, zapp.parameters, self.current_user.role)

        try:
            self.get_argument('download_json')
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition', 'attachment; filename={}.json'.format(zapp_id))
            self.write(app_descr)
            self.finish()
            return
        except MissingArgumentError:
            new_id = self.api_endpoint.execution_start(self.current_user, exec_name, app_descr)

        self.redirect(self.reverse_url('execution_inspect', new_id))

    def _set_parameters(self, app_descr, params, role):
        for param in params:
            argument_name = param.name + '-' + param.kind
            if param.kind == 'environment':
                for service in app_descr['services']:
                    for env in service['environment']:
                        if env[0] == param.name:
                            env[1] = self.get_argument(argument_name)
            elif param.kind == 'command':
                for service in app_descr['services']:
                    if service['name'] == param.name:
                        service['command'] = self.get_argument(argument_name)
                        break
            else:
                log.warning('Unknown parameter kind: {}, ignoring...'.format(param.kind))

        if role == "admin" or (role != "guest" and (role == "user" and not get_conf().no_user_edit_limits_web)):
            for service in app_descr['services']:
                argument_name = service['name'] + '-resource_memory_min'
                try:
                    self.get_argument(argument_name)
                except MissingArgumentError:
                    pass
                else:
                    if float(self.get_argument(argument_name)) >= get_conf().max_memory_limit:
                        val = int(get_conf().max_memory_limit * (1024 ** 3))
                    else:
                        val = int(float(self.get_argument(argument_name)) * (1024 ** 3))
                    service["resources"]["memory"]["min"] = val

                argument_name = service['name'] + '-resource_cores_min'
                try:
                    self.get_argument(argument_name)
                except MissingArgumentError:
                    pass
                else:
                    if float(self.get_argument(argument_name)) >= get_conf().max_core_limit:
                        val = get_conf().max_core_limit
                    else:
                        val = float(self.get_argument(argument_name))
                    service["resources"]["cores"]["min"] = val
                    break

        return app_descr
