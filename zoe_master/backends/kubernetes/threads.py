# Copyright (c) 2017, Quang-Nhat Hoang-Xuan
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

"""Monitor for the Kubernetes event stream."""

import logging
import threading
import time

from zoe_lib.config import get_conf
from zoe_lib.state import SQLManager, Service
from zoe_master.backends.kubernetes.api_client import KubernetesClient

log = logging.getLogger(__name__)


class KubernetesMonitor(threading.Thread):
    """The monitor."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('monitor')
        self.stop = False
        self.state = state
        self.setDaemon(True)
        self.service_id = {}
        self.kube = KubernetesClient(get_conf())
        self.start()

    def run(self):
        """An infinite loop that listens for events from Kubernetes."""
        log.info("Monitor thread started")
        while True:  # pylint: disable=too-many-nested-blocks
            for event in self.kube.replication_controller_event():
                log.debug('%s: %s', event.object.name, event.type)
                if event.type != 'DELETED' and event.type != 'ADDED':
                    rc_info = self.kube.inspect_replication_controller(event.object.name)
                    if rc_info:
                        rc_uid = rc_info['backend_id']
                        service = self.state.service_list(only_one=True, backend_id=rc_uid)
                        if event.object.name not in self.service_id:
                            self.service_id[event.object.name] = service.id
                        if service is not None:
                            if rc_info['readyReplicas'] == 0:
                                log.debug('Number replicas: 0')
                                service.set_backend_status(service.BACKEND_UNDEFINED_STATUS)
                            elif rc_info['readyReplicas'] < rc_info['replicas']:
                                logstr = 'Number replicas: ' + str(rc_info['readyReplicas'])
                                log.debug(logstr)
                                service.set_backend_status(service.BACKEND_CREATE_STATUS)
                            elif rc_info['readyReplicas'] == rc_info['replicas']:
                                if service.backend_status != service.BACKEND_START_STATUS:
                                    log.debug('Reached desired number of replicas')
                                    service.set_backend_status(service.BACKEND_START_STATUS)
                else:
                    if event.type != 'ADDED':
                        if event.object.name in self.service_id:
                            sid = self.service_id[event.object.name]
                            self.service_id.pop(event.object.name)
                            service = self.state.service_list(only_one=True, id=sid)
                            if service is not None:
                                log.info('Destroyed all replicas')
                                service.set_backend_status(service.BACKEND_DESTROY_STATUS)
                time.sleep(1)

            time.sleep(2)

    def quit(self):
        """Stops the thread."""
        self.stop = True


CHECK_INTERVAL = 300


class KubernetesStateSynchronizer(threading.Thread):
    """The Kubernetes Checker."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('checker')
        self.stop = False
        self.state = state
        self.setDaemon(True)
        self.kube = KubernetesClient(get_conf())
        self.start()

    def _find_dead_service(self, repcon_list, service: Service):
        """Loop through the pods and try to update the service status."""
        found = False
        for rep in repcon_list:
            if rep['backend_id'] == service.backend_id:
                found = True
                if rep['running'] is False:
                    log.info('resetting status of service {}, died with no event'.format(service.name))
                    service.set_backend_status(service.BACKEND_DIE_STATUS)
        if not found:
            service.set_backend_status(service.BACKEND_DESTROY_STATUS)

    def run(self):
        """The thread loop."""
        log.info("Checker thread started")
        while not self.stop:
            service_list = self.state.service_list()
            repcon_list = self.kube.replication_controller_list()
            for service in service_list:
                assert isinstance(service, Service)
                if service.backend_status == service.BACKEND_DESTROY_STATUS or service.backend_status == service.BACKEND_DIE_STATUS:
                    continue
                self._find_dead_service(repcon_list, service)

            time.sleep(CHECK_INTERVAL)

    def quit(self):
        """Stops the thread."""
        self.stop = True
