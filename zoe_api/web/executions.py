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
from zoe_api.web.request_handler import ZoeWebRequestHandler


class ExecutionStartWeb(ZoeWebRequestHandler):
    """Handler class"""

    def post(self):
        """Start an execution."""
        if self.current_user is None:
            return

        app_descr_json = self.request.files['file'][0]['body'].decode('utf-8')
        app_descr = json.loads(app_descr_json)
        exec_name = self.get_argument('exec_name')

        try:
            new_id = self.api_endpoint.execution_start(self.current_user, exec_name, app_descr)
        except zoe_api.exceptions.ZoeException as e:
            self.error_page(error_message=e.message)
            return

        self.redirect(self.reverse_url('execution_inspect', new_id))


class ExecutionListWeb(ZoeWebRequestHandler):
    """Handler class"""
    PAGINATION_ITEM_COUNT = 50

    def get(self, page=0):
        """Home page with authentication."""
        if self.current_user is None:
            return

        page = int(page)
        executions_count = self.api_endpoint.execution_count(self.current_user)
        executions = self.api_endpoint.execution_list(self.current_user, base=page*self.PAGINATION_ITEM_COUNT, limit=self.PAGINATION_ITEM_COUNT)

        template_vars = {
            "user": self.current_user,
            'executions': sorted(executions, key=lambda e: e.id, reverse=True),
            'current_page': page,
            'max_page': math.ceil(executions_count / self.PAGINATION_ITEM_COUNT),
            'last_page': len(executions) < self.PAGINATION_ITEM_COUNT
        }
        self.render('execution_list.jinja2', **template_vars)


class ExecutionRestartWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self, execution_id: int):
        """Restart an already defined (and not running) execution."""
        if self.current_user is None:
            return

        try:
            e = self.api_endpoint.execution_by_id(self.current_user, execution_id)
            new_id = self.api_endpoint.execution_start(self.current_user, e.name, e.description)
        except zoe_api.exceptions.ZoeException as e:
            self.error_page(error_message=e.message)
            return

        self.redirect(self.reverse_url('execution_inspect', new_id))


class ExecutionTerminateWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self, execution_id: int):
        """Terminate an execution."""
        if self.current_user is None:
            return

        try:
            self.api_endpoint.execution_terminate(self.current_user, execution_id)
        except zoe_api.exceptions.ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.redirect(self.reverse_url('home_user'))


class ExecutionInspectWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self, execution_id):
        """Gather details about an execution."""
        if self.current_user is None:
            return

        try:
            e = self.api_endpoint.execution_by_id(self.current_user, execution_id)
        except zoe_api.exceptions.ZoeException as ex:
            self.set_status(ex.status_code, ex.message)
            return

        services_info, endpoints = self.api_endpoint.execution_endpoints(self.current_user, e)

        template_vars = {
            "e": e,
            "services_info": services_info,
            "endpoints": endpoints,
            'killed_at': e.time_submit + datetime.timedelta(hours=e.owner.quota.runtime_limit)
        }

        if get_conf().enable_plots and e.time_start is not None:
            grafana_url_template = 'https://cloud-platform.eurecom.fr/grafana/dashboard/db/zoe-executions?orgId=1&from={}&to={}&var-execution_id={}&refresh=1y'
            if e.time_end is None:
                e_time_end = int(time.time() * 1000)
            else:
                e_time_end = int((e.time_end - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1) * 1000)
            e_time_start = int((e.time_start - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1) * 1000)
            template_vars['grafana_url'] = grafana_url_template.format(e_time_start, e_time_end, execution_id)

        self.render('execution_inspect.jinja2', **template_vars)


class ServiceLogsWeb(ZoeWebRequestHandler):
    """Handler class"""

    def get(self, service_id):
        """Gather details about an execution."""
        if self.current_user is None:
            return

        try:
            service = self.api_endpoint.service_by_id(self.current_user, service_id)
        except zoe_api.exceptions.ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        template_vars = {
            "service": service,
            "websocket_base": get_conf().websocket_base + get_conf().reverse_proxy_path
        }
        self.render('service_logs.jinja2', **template_vars)
