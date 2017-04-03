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

from tornado.web import RequestHandler
import tornado.escape

from zoe_api.rest_api.utils import catch_exceptions, get_auth, manage_cors_headers
import zoe_api.exceptions
from zoe_api.api_endpoint import APIEndpoint  # pylint: disable=unused-import


class ExecutionAPI(RequestHandler):
    """The Execution API endpoint."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    def options(self, execution_id):  # pylint: disable=unused-argument
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def get(self, execution_id):
        """GET a single execution by its ID."""
        uid, role = get_auth(self)

        e = self.api_endpoint.execution_by_id(uid, role, execution_id)

        self.write(e.serialize())

    @catch_exceptions
    def delete(self, execution_id: int):
        """
        Terminate an execution.

        :param execution_id: the execution to be terminated
        """
        uid, role = get_auth(self)

        success, message = self.api_endpoint.execution_terminate(uid, role, execution_id)
        if not success:
            raise zoe_api.exceptions.ZoeRestAPIException(message, 400)

        self.set_status(204)

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass


class ExecutionDeleteAPI(RequestHandler):
    """The ExecutionDelete API endpoints."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    @catch_exceptions
    def options(self, execution_id):  # pylint: disable=unused-argument
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def delete(self, execution_id: int):
        """
        Delete an execution.

        :param execution_id: the execution to be deleted
        """
        uid, role = get_auth(self)

        success, message = self.api_endpoint.execution_delete(uid, role, execution_id)
        if not success:
            raise zoe_api.exceptions.ZoeRestAPIException(message, 400)

        self.set_status(204)

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass


class ExecutionCollectionAPI(RequestHandler):
    """The Execution Collection API endpoints."""

    def initialize(self, **kwargs):
        """Initializes the request handler."""
        self.api_endpoint = kwargs['api_endpoint']  # type: APIEndpoint

    def set_default_headers(self):
        """Set up the headers for enabling CORS."""
        manage_cors_headers(self)

    @catch_exceptions
    def options(self):  # pylint: disable=unused-argument
        """Needed for CORS."""
        self.set_status(204)
        self.finish()

    @catch_exceptions
    def get(self):
        """
        Returns a list of all active executions.

        Return a list of all executions which have status equal to ..."

        example:  curl -u 'username:password' -X GET -H "Content-Type: application/json" -d '{"status":"terminated"}' http://bf5:8080/api/0.6/execution

        :return:
        """
        uid, role = get_auth(self)

        filt_dict = {}

        try:
            if self.request.body:
                filt_dict = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        if 'status' in filt_dict:
            execs = self.api_endpoint.execution_list(uid, role, status=filt_dict['status'])
        else:
            execs = self.api_endpoint.execution_list(uid, role)

        self.write(dict([(e.id, e.serialize()) for e in execs]))

    @catch_exceptions
    def post(self):
        """
        Starts an execution, given an application description. Takes a JSON object.

        :return: the new execution_id
        """
        uid, role = get_auth(self)

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        application_description = data['application']
        exec_name = data['name']

        new_id = self.api_endpoint.execution_start(uid, role, exec_name, application_description)

        self.set_status(201)
        self.write({'execution_id': new_id})

    def data_received(self, chunk):
        """Not implemented as we do not use stream uploads"""
        pass
