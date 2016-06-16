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

import logging
import time

from flask_restful import Resource, request

from zoe_lib.exceptions import ZoeRestAPIException
from zoe_web.config import singletons
from zoe_web.rest_api.utils import catch_exceptions

log = logging.getLogger(__name__)


class ServiceAPI(Resource):
    @catch_exceptions
    def get(self, container_id):
        start_time = time.time()
        calling_user = authenticate(request, self.state)

        c = self.state.get_one('service', id=container_id)
        if c is None:
            raise ZoeRestAPIException('No such service', 404)

        is_authorized(calling_user, c, 'get')
        singletons['metric'].metric_api_call(start_time, 'service', 'get', calling_user)
        return c.to_dict(checkpoint=False)

    @catch_exceptions
    def delete(self, container_id):
        start_time = time.time()
        calling_user = authenticate(request, self.state)

        c = self.state.get_one('service', id=container_id)
        if c is None:
            raise ZoeRestAPIException('No such service', 404)

        is_authorized(calling_user, c, 'delete')

        if c.is_monitor:
            log.info("Monitor service died ({}), terminating execution {}".format(c.name, c.execution.name))
            self.platform.execution_terminate(c.execution, reason='finished')
            self.state.state_updated()
        else:
            # FIXME: A non-fundamental service died, nothing we can do?
            # We leave everything in place, so when the execution terminates we will
            # gather the logs also of the services that died
            log.warning("Service {} died by itself".format(c.name))

        singletons['metric'].metric_api_call(start_time, 'service', 'get', calling_user)
        return '', 204
