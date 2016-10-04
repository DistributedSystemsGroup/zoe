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

"""Web pages and functions related to executions."""

import json

import zoe_api.exceptions
from zoe_api.web.utils import get_auth, catch_exceptions
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.custom_request_handler import ZoeRequestHandler


class ExecutionDefineWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self):
        """Define a new execution."""
        get_auth(self)

        self.render('execution_new.html')


class ExecutionStartWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def post(self):
        """Start an execution."""
        uid, role = get_auth(self)

        app_descr_json = self.request.files['file'][0]['body'].decode('utf-8')
        app_descr = json.loads(app_descr_json)
        exec_name = self.get_argument('exec_name')

        new_id = self.api_endpoint.execution_start(uid, role, exec_name, app_descr)

        self.redirect(self.reverse_url('execution_inspect', new_id))


class ExecutionRestartWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, execution_id: int):
        """Restart an already defined (and not running) execution."""
        uid, role = get_auth(self)

        e = self.api_endpoint.execution_by_id(uid, role, execution_id)
        new_id = self.api_endpoint.execution_start(uid, role, e.name, e.description)

        self.redirect(self.reverse_url('execution_inspect', new_id))


class ExecutionTerminateWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, execution_id: int):
        """Terminate an execution."""
        uid, role = get_auth(self)

        success, message = self.api_endpoint.execution_terminate(uid, role, execution_id)
        if not success:
            raise zoe_api.exceptions.ZoeException(message)

        self.redirect(self.reverse_url('home_user'))


class ExecutionDeleteWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, execution_id: int):
        """Delete an execution."""
        uid, role = get_auth(self)

        success, message = self.api_endpoint.execution_delete(uid, role, execution_id)
        if not success:
            raise zoe_api.exceptions.ZoeException(message)

        self.redirect(self.reverse_url('home_user'))


class ExecutionInspectWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, execution_id):
        """Gather details about an execution."""
        uid, role = get_auth(self)

        e = self.api_endpoint.execution_by_id(uid, role, execution_id)

        services_info = []
        for service in e.services:
            services_info.append(self.api_endpoint.service_by_id(uid, role, service.id))

        template_vars = {
            "e": e,
            "services_info": services_info
        }
        self.render('execution_inspect.html', **template_vars)
