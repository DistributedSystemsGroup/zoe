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

"""Web pages and functions related to executions."""

import datetime
import json
import math
import time

from zoe_lib.config import get_conf

import zoe_api.exceptions
from zoe_api.web.utils import get_auth, catch_exceptions
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import
from zoe_api.web.custom_request_handler import ZoeRequestHandler


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
        if uid is None:
            self.redirect(self.get_argument('next', u'/login'))
            return

        app_descr_json = self.request.files['file'][0]['body'].decode('utf-8')
        app_descr = json.loads(app_descr_json)
        exec_name = self.get_argument('exec_name')

        new_id = self.api_endpoint.execution_start(uid, role, exec_name, app_descr)

        self.redirect(self.reverse_url('execution_inspect', new_id))


class ExecutionListWeb(ZoeRequestHandler):
    """Handler class"""
    PAGINATION_ITEM_COUNT = 50

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, page=0):
        """Home page with authentication."""
        uid, role = get_auth(self)
        if uid is None:
            self.redirect(self.get_argument('next', u'/login'))
            return

        page = int(page)
        executions_count = self.api_endpoint.execution_count(uid, role)
        executions = self.api_endpoint.execution_list(uid, role, base=page*self.PAGINATION_ITEM_COUNT, limit=self.PAGINATION_ITEM_COUNT)

        template_vars = {
            "uid": uid,
            "role": role,
            'executions': sorted(executions, key=lambda e: e.id, reverse=True),
            'current_page': page,
            'max_page': math.ceil(executions_count / self.PAGINATION_ITEM_COUNT),
            'last_page': len(executions) < self.PAGINATION_ITEM_COUNT
        }
        self.render('execution_list.html', **template_vars)


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
        if uid is None:
            self.redirect(self.get_argument('next', u'/login'))
            return

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
        if uid is None:
            self.redirect(self.get_argument('next', u'/login'))
            return

        success, message = self.api_endpoint.execution_terminate(uid, role, execution_id)
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
        if uid is None:
            self.redirect(self.get_argument('next', u'/login'))
            return

        e = self.api_endpoint.execution_by_id(uid, role, execution_id)

        services_info, endpoints = self.api_endpoint.execution_endpoints(uid, role, e)

        endpoints = self.api_endpoint.execution_endpoints(uid, role, e)[1]

        template_vars = {
            "uid": uid,
            "role": role,
            "e": e,
            "services_info": services_info,
            "endpoints": endpoints,
        }

        if get_conf().enable_plots and e.time_start is not None:
            grafana_url_template = 'http://bigfoot-m2.eurecom.fr/grafana/dashboard/db/zoe-executions?orgId=1&from={}&to={}&var-execution_id={}&refresh=1y'
            if e.time_end is None:
                e_time_end = int(time.time() * 1000)
            else:
                e_time_end = int((e.time_end - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1) * 1000)
            e_time_start = int((e.time_start - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1) * 1000)
            template_vars['grafana_url'] = grafana_url_template.format(e_time_start, e_time_end, execution_id)

        self.render('execution_inspect.html', **template_vars)


class ServiceLogsWeb(ZoeRequestHandler):
    """Handler class"""
    def initialize(self, **kwargs):
        """Initializes the request handler."""
        super().initialize(**kwargs)
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    @catch_exceptions
    def get(self, service_id):
        """Gather details about an execution."""
        uid, role = get_auth(self)
        if uid is None:
            self.redirect(self.get_argument('next', u'/login'))
            return

        service = self.api_endpoint.service_by_id(uid, role, service_id)

        template_vars = {
            "uid": uid,
            "role": role,
            "service": service,
        }
        self.render('service_logs.html', **template_vars)
