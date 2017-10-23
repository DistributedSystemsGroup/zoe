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
from zoe_master.backends.docker.api_client import DockerClient
from zoe_master.backends.docker.config import DockerConfig, DockerHostConfig  # pylint: disable=unused-import
from zoe_master.exceptions import ZoeException

log = logging.getLogger(__name__)

CHECK_INTERVAL = 10


class DockerStateSynchronizer(threading.Thread):
    """The Docker Checker."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('checker')
        self.stop = threading.Event()
        self.my_stop = threading.Event()
        self.state = state
        self.setDaemon(True)
        self.host_checkers = []
        for docker_host in DockerConfig(get_conf().backend_docker_config_file).read_config():
            th = threading.Thread(target=self._host_subthread, args=(docker_host,), name='synchro_' + docker_host.name, daemon=True)
            th.start()
            self.host_checkers.append((th, docker_host))

        self.start()

    def _host_subthread(self, host_config: DockerHostConfig):
        log.info("Synchro thread for host {} started".format(host_config.name))

        node_status = 'offline'
        while True:
            ret = self.stop.wait(timeout=CHECK_INTERVAL)
            if ret:
                break
            try:
                my_engine = DockerClient(host_config)
            except ZoeException as e:
                node_status = 'offline'
                log.error(str(e))
                log.info('Node {} is offline'.format(host_config.name))
                time.sleep(CHECK_INTERVAL)
                continue
            if node_status == 'offline':
                log.info('Node {} is now online'.format(host_config.name))
            node_status = 'online'

            try:
                container_list = my_engine.list(only_label={'zoe_deployment_name': get_conf().deployment_name})
            except ZoeException:
                continue

            for cont in container_list:
                service = self.state.service_list(only_one=True, backend_host=host_config.name, backend_id=cont['id'])
                if service is None:
                    log.warning('Container {} on host {} has no corresponding service'.format(cont['name'], host_config.name))
                    continue
                self._update_service_status(service, cont)
        log.info("Synchro thread for host {} stopped".format(host_config.name))

    def _update_service_status(self, service: Service, container):
        """Update the service status."""
        if service.backend_status != container['state']:
            old_status = service.backend_status
            service.set_backend_status(container['state'])
            log.debug('Updated service status, {} from {} to {}'.format(service.name, old_status, container['state']))

    def run(self):
        """The thread loop."""
        log.info("Checker thread started")
        while True:
            ret = self.my_stop.wait(timeout=CHECK_INTERVAL)
            if ret:
                break
            to_remove = []
            to_add = []
            for th, conf in self.host_checkers:
                if not th.is_alive():
                    log.warning('Thread {} has died, starting a new one.'.format(th.name))
                    to_remove.append((th, conf))
                    th = threading.Thread(target=self._host_subthread, args=(conf,), name='synchro_' + conf.name, daemon=True)
                    th.start()
                    to_add.append((th, conf))
            for dead_th in to_remove:
                self.host_checkers.remove(dead_th)
            for new_th in to_add:
                self.host_checkers.append(new_th)
        log.info("Checker thread stopped")

    def quit(self):
        """Stops the thread."""
        self.stop.set()
        for th, conf_ in self.host_checkers:
            th.join()
        self.my_stop.set()
        self.join()
