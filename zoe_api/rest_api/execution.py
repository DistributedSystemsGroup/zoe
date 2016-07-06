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

from flask_restful import Resource, request
from werkzeug.exceptions import BadRequest

from zoe_api.rest_api.utils import catch_exceptions, get_auth
import zoe_api.exceptions
import zoe_api.api_endpoint


class ExecutionAPI(Resource):
    """The Execution API endpoint."""

    def __init__(self, api_endpoint: zoe_api.api_endpoint.APIEndpoint) -> None:
        self.api_endpoint = api_endpoint

    @catch_exceptions
    def get(self, execution_id):
        """GET a single execution by its ID."""
        uid, role = get_auth(request)

        e = self.api_endpoint.execution_by_id(uid, role, execution_id)

        return e.serialize()

    @catch_exceptions
    def delete(self, execution_id: int):
        """
        Terminate an execution.

        :param execution_id: the execution to be terminated
        :return:
        """
        uid, role = get_auth(request)

        success, message = self.api_endpoint.execution_terminate(uid, role, execution_id)
        if not success:
            raise zoe_api.exceptions.ZoeRestAPIException(message, 400)

        return '', 204


class ExecutionDeleteAPI(Resource):
    """The ExecutionDelete API endpoints."""

    def __init__(self, api_endpoint: zoe_api.api_endpoint.APIEndpoint) -> None:
        self.api_endpoint = api_endpoint

    @catch_exceptions
    def delete(self, execution_id: int):
        """
        Delete an execution.

        :param execution_id: the execution to be deleted
        :return:
        """
        uid, role = get_auth(request)

        success, message = self.api_endpoint.execution_delete(uid, role, execution_id)
        if not success:
            raise zoe_api.exceptions.ZoeRestAPIException(message, 400)

        return '', 204


class ExecutionCollectionAPI(Resource):
    """The Execution Collection API endpoints."""

    def __init__(self, api_endpoint: zoe_api.api_endpoint.APIEndpoint) -> None:
        self.api_endpoint = api_endpoint

    @catch_exceptions
    def get(self):
        """
        Returns a list of all active executions.

        :return:
        """
        uid, role = get_auth(request)

        execs = self.api_endpoint.execution_list(uid, role)
        return [e.serialize() for e in execs]

    @catch_exceptions
    def post(self):
        """
        Starts an execution, given an application description. Takes a JSON object.
        :return: the new execution_id
        """
        uid, role = get_auth(request)

        try:
            data = request.get_json()
        except BadRequest:
            raise zoe_api.exceptions.ZoeRestAPIException('Error decoding JSON data')

        application_description = data['application']
        exec_name = data['name']

        new_id = self.api_endpoint.execution_start(uid, role, exec_name, application_description)

        return {'execution_id': new_id}, 201
