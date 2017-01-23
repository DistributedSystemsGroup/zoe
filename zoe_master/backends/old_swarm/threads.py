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

"""Monitor for the Swarm event stream."""

import logging
import threading
import time

from zoe_lib.config import get_conf
from zoe_lib.state import SQLManager, Service
from zoe_master.backends.old_swarm.api_client import SwarmClient

log = logging.getLogger(__name__)


class SwarmMonitor(threading.Thread):
    """The monitor."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('monitor')
        self.stop = False
        self.state = state
        self.setDaemon(True)

        self.start()

    def run(self):
        """The thread loop."""
        log.info("Monitor thread started")
        swarm = SwarmClient(get_conf())
        while True:
            try:
                swarm.event_listener(lambda x: self._event_cb(x))
            except Exception:
                log.exception('Exception in monitor thread')
            time.sleep(1)  # wait a bit before retrying the connection

    def _event_cb(self, event: dict) -> bool:
        if event['Type'] == 'container':
            self._container_event(event)
        else:
            log.debug('Unmanaged event type: {}'.format(event['Type']))
            log.debug(str(event))

        if self.stop:
            return False
        else:
            return True

    def _container_event(self, event: dict):
        if 'zoe.deployment_name' not in event['Actor']['Attributes']:
            return
        if event['Actor']['Attributes']['zoe.deployment_name'] != get_conf().deployment_name:
            return

        service_id = event['Actor']['Attributes']['zoe.service.id']  # type: int
        service = self.state.service_list(only_one=True, id=service_id)
        if service is None:
            return
        if 'create' in event['Action']:
            service.set_backend_status(service.BACKEND_CREATE_STATUS)
        elif 'start' in event['Action']:
            service.set_backend_status(service.BACKEND_START_STATUS)
        elif 'die' in event['Action'] or 'kill' in event['Action'] or 'stop' in event['Action']:
            service.set_backend_status(service.BACKEND_DIE_STATUS)
        elif 'oom' in event['Action']:
            service.set_backend_status(service.BACKEND_OOM_STATUS)
            log.warning('Service {} got killed by an OOM condition'.format(service.id))
        elif 'destroy' in event['Action']:
            service.set_backend_status(service.BACKEND_DESTROY_STATUS)
        else:
            log.debug('Unmanaged container action: {}'.format(event['Action']))

    def quit(self):
        """Stops the thread."""
        self.stop = True


CHECK_INTERVAL = 300


class SwarmStateSynchronizer(threading.Thread):
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
                if service.backend_status == service.BACKEND_DESTROY_STATUS or service.backend_status == service.BACKEND_DIE_STATUS:
                    continue
                found = False
                for container in container_list:
                    if container['id'] == service.backend_id:
                        found = True
                        if container['status'] == 'exited':
                            log.info('resetting status of service {}, died with no event'.format(service.name))
                            service.set_backend_status(service.BACKEND_DIE_STATUS)
                if not found:
                    service.set_backend_status(service.BACKEND_DESTROY_STATUS)

            time.sleep(CHECK_INTERVAL)

    def quit(self):
        """Stops the thread."""
        self.stop = True
