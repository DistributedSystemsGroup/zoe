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
This module contains all container-related API calls that a Zoe client can use.
"""
import logging

from zoe_lib import ZoeAPIBase
from zoe_lib.exceptions import ZoeAPIException

log = logging.getLogger(__name__)


class ZoeContainerAPI(ZoeAPIBase):
    """
    The container API class. Containers are read-only objects. The delete operation merely informs the master that a container has died outside of its control.
    """
    def get(self, container_id: int) -> dict:
        """
        Retrieve container state.

        :param container_id: the container to query
        :return:
        """
        c, status_code = self._rest_get('/container/' + str(container_id))
        if status_code == 200:
            return c
        elif status_code == 404:
            raise ZoeAPIException('container "{}" not found'.format(container_id))
        else:
            raise ZoeAPIException('error retrieving container {}'.format(container_id))

    def log(self, container_id: int) -> str:
        """
        Get the standard output/error of the processes running in the given container.

        :param container_id: the container to examine
        :return: a string containing the log
        """
        q = {
            'what': 'container logs',
            'filters': {'id': container_id}
        }

        data, status_code = self._rest_post('/query', q)
        if status_code != 200:
            raise ZoeAPIException(data['message'])
        else:
            return data[0]

    def stats(self, container_id: int) -> dict:
        """
        Get low-level statistics about a container. These come directly from Docker.

        :param container_id: The container to examine
        :return: the statistics. The format of this dictionary is not set in stone and could change.
        """
        q = {
            'what': 'container stats',
            'filters': {'id': container_id}
        }

        data, status_code = self._rest_post('/query', q)
        if status_code != 200:
            raise ZoeAPIException(data['message'])
        else:
            return data

    def died(self, container_id: int):
        """
        Inform the master that a container died. Used by the observer process.

        :param container_id: Zoe ID of the container that died
        :return:
        """
        data, status_code = self._rest_delete('/container/{}'.format(container_id))
        if status_code != 204:
            raise ZoeAPIException(data['message'])
