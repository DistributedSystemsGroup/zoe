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

from flask_restful import Resource, request
from werkzeug.exceptions import BadRequest

from zoe_web.exceptions import ZoeRestAPIException
import zoe_web.config as config
import zoe_web.api_endpoint
from zoe_web.rest_api.utils import catch_exceptions, get_auth


class QueryAPI(Resource):
    @catch_exceptions
    def post(self):
        uid, role = get_auth(request)
        assert isinstance(config.api_endpoint, zoe_web.api_endpoint.APIEndpoint)

        try:
            data = request.get_json()
        except BadRequest:
            raise ZoeRestAPIException('Error decoding JSON data')

        if 'what' not in data:
            raise ZoeRestAPIException('"what" is required in query object')

        what = data['what']
        if 'filters' not in data:
            filters = {}
        else:
            filters = data['filters']

        if not isinstance(filters, dict):
            raise ZoeRestAPIException('query filters should be a dictionary of {attribute: requested_value} entries')

        if what == 'stats_scheduler':
            # TODO
            ret = None
        elif what == 'execution':
            if role != 'admin':
                filters['user_id'] = uid
            execs = config.api_endpoint.execution_list(uid, role, filters)
            return [x.serialize() for x in execs]
        else:
            raise ZoeRestAPIException('unknown query {}'.format(what))

        return ret
