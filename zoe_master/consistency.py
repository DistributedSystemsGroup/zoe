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

"""Periodically try to integrate Swarm state into Zoe, since Swarm event stream fails randomly."""

import logging
import threading
import time

from zoe_lib.swarm_client import SwarmClient
from zoe_lib.config import get_conf
from zoe_lib.sql_manager import SQLManager, Service

log = logging.getLogger(__name__)

CHECK_INTERVAL = 300


class ZoeSwarmChecker(threading.Thread):
    """The Swarm Checker."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('checker')
        self.stop = False
        self.state = state
        self.setDaemon(True)

        self.start()

    def run(self):
        """The thread loop."""
        log.info("Checker thread started")
        swarm = SwarmClient(get_conf())
        while not self.stop:
            service_list = self.state.service_list()
            container_list = swarm.list(only_label={'zoe.deployment_name': get_conf().deployment_name})

            for service in service_list:
                assert isinstance(service, Service)
                if service.docker_status == service.DOCKER_DESTROY_STATUS or service.docker_status == service.DOCKER_DIE_STATUS:
                    continue
                found = False
                for container in container_list:
                    if container['id'] == service.docker_id:
                        found = True
                        if container['status'] == 'exited':
                            log.info('resetting status of service {}, died with no event'.format(service.name))
                            service.set_docker_status(service.DOCKER_DIE_STATUS)
                if not found:
                    service.set_docker_status(service.DOCKER_DESTROY_STATUS)

            time.sleep(CHECK_INTERVAL)

    def quit(self):
        """Stops the thread."""
        self.stop = True
