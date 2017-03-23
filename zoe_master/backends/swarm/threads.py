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

"""Monitor for the Swarm event stream."""

import logging
import threading
import time

from zoe_lib.config import get_conf
from zoe_lib.state import SQLManager, Service
from zoe_master.backends.swarm.api_client import SwarmClient
from zoe_master.exceptions import ZoeException

log = logging.getLogger(__name__)

CHECK_INTERVAL = 10


class SwarmStateSynchronizer(threading.Thread):
    """The Swarm Checker."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('checker')
        self.stop = False
        self.state = state
        self.setDaemon(True)

        self.start()

    def _update_service_status(self, service: Service, container):
        """Update the service status."""
        if service.backend_status != container['state']:
            old_status = service.backend_status
            service.set_backend_status(container['state'])
            log.debug('Updated service status, {} from {} to {}'.format(service.name, old_status, container['state']))

    def run(self):
        """The thread loop."""
        log.info("Checker thread started")
        while not self.stop:
            swarm = SwarmClient()
            service_list = self.state.service_list()
            try:
                container_list = swarm.list(only_label={'zoe_deployment_name': get_conf().deployment_name})
            except ZoeException:
                continue
            containers = {}
            for cont in container_list:
                containers[cont['id']] = cont

            services = {}
            for serv in service_list:
                services[serv.backend_id] = serv

            for service in service_list:
                assert isinstance(service, Service)
                if service.backend_id in containers:
                    self._update_service_status(service, containers[service.backend_id])
                else:
                    if service.backend_status == service.BACKEND_DESTROY_STATUS:
                        continue
                    else:
                        service.set_backend_status(service.BACKEND_DESTROY_STATUS)

            time.sleep(CHECK_INTERVAL)

    def quit(self):
        """Stops the thread."""
        self.stop = True
