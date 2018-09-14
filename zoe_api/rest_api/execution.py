# Copyright (c) 2016, Daniele Venzano
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

"""The Execution API endpoints."""

import tornado.escape

from zoe_api.rest_api.request_handler import ZoeAPIRequestHandler
from zoe_api.exceptions import ZoeException


class ExecutionAPI(ZoeAPIRequestHandler):
    """The Execution API endpoint."""

    def get(self, execution_id):
        """GET a single execution by its ID."""
        if self.current_user is None:
            return

        try:
            e = self.api_endpoint.execution_by_id(self.current_user, execution_id)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.write(e.serialize())

    def delete(self, execution_id: int):
        """
        Terminate an execution.

        :param execution_id: the execution to be terminated
        """
        if self.current_user is None:
            return

        try:
            self.api_endpoint.execution_terminate(self.current_user, execution_id, 'user {} request from API'.format(self.current_user))
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
        else:
            self.set_status(204)


class ExecutionDeleteAPI(ZoeAPIRequestHandler):
    """The ExecutionDelete API endpoints."""

    def delete(self, execution_id: int):
        """
        Delete an execution.

        :param execution_id: the execution to be deleted
        """
        if self.current_user is None:
            return

        try:
            self.api_endpoint.execution_delete(self.current_user, execution_id)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
        else:
            self.set_status(204)


class ExecutionCollectionAPI(ZoeAPIRequestHandler):
    """The Execution Collection API endpoints."""

    def get(self):
        """
        Returns a list of all active executions.

        The list can be filtered by passing a non-empty JSON dictionary. Any combination of the following filters is supported:

        * status: one of submitted, queued, starting, error, running, cleaning up, terminated
        * name: execution mane
        * user_id: user_id owning the execution (admin only)
        * limit: limit the number of returned entries
        * earlier_than_submit: all execution that where submitted earlier than this timestamp
        * earlier_than_start: all execution that started earlier than this timestamp
        * earlier_than_end: all execution that ended earlier than this timestamp
        * later_than_submit: all execution that where submitted later than this timestamp
        * later_than_start: all execution that started later than this timestamp
        * later_than_end: all execution that started later than this timestamp

        All timestamps should be passed as number of seconds since the epoch (UTC timezone).

        example:  curl -u 'username:password' -X GET 'http://bf5:8080/api/0.6/execution?limit=1&status=terminated'

        :return:
        """
        if self.current_user is None:
            return

        filt_dict = {}

        filters = [
            ('status', str),
            ('name', str),
            ('user_id', str),
            ('limit', int),
            ('earlier_than_submit', int),
            ('earlier_than_start', int),
            ('earlier_than_end', int),
            ('later_than_submit', int),
            ('later_than_start', int),
            ('later_than_end', int)
        ]
        for filt in filters:
            if filt[0] in self.request.arguments:
                if filt[1] == str:
                    filt_dict[filt[0]] = self.request.arguments[filt[0]][0].decode('utf-8')
                else:
                    filt_dict[filt[0]] = filt[1](self.request.arguments[filt[0]][0])

        try:
            execs = self.api_endpoint.execution_list(self.current_user, **filt_dict)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.write({e.id: e.serialize() for e in execs})

    def post(self):
        """
        Starts an execution, given an application description. Takes a JSON object.

        :return: the new execution_id
        """
        if self.current_user is None:
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            self.set_status(400, 'Error decoding JSON data')
            return

        application_description = data['application']
        exec_name = data['name']

        try:
            new_id = self.api_endpoint.execution_start(self.current_user, exec_name, application_description)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.set_status(201)
        self.write({'execution_id': new_id})


class ExecutionEndpointsAPI(ZoeAPIRequestHandler):
    """The ExecutionEndpoints API endpoint."""

    def get(self, execution_id: int):
        """
        Get a list of execution endpoints.

        :param execution_id: the execution to be deleted
        """
        if self.current_user is None:
            return

        try:
            execution = self.api_endpoint.execution_by_id(self.current_user, execution_id)
            services_, endpoints = self.api_endpoint.execution_endpoints(self.current_user, execution)
        except ZoeException as e:
            self.set_status(e.status_code, e.message)
            return

        self.write({'endpoints': endpoints})
