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

"""
This module contains all service-related API calls that a Zoe client can use.
"""
import logging

from zoe_lib.api_base import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeServiceAPI(ZoeAPIBase):
    """
    The service API class. Services are read-only objects. The delete operation merely informs the master that a service has died outside of its control.
    """
    def get(self, container_id):
        """
        Retrieve service state.

        :param container_id: the service to query
        :return:

        :type container_id: int
        :rtype: dict
        """
        cont, status_code = self._rest_get('/service/' + str(container_id))
        if status_code == 200:
            return cont
        elif status_code == 404:
            raise ZoeAPIException('service "{}" not found'.format(container_id))
        else:
            raise ZoeAPIException('error retrieving service {}'.format(container_id))
