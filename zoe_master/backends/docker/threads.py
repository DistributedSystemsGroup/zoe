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
from zoe_master.stats import NodeStats

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
        self.host_stats = {}
        for docker_host in DockerConfig(get_conf().backend_docker_config_file).read_config():
            th = threading.Thread(target=self._host_subthread, args=(docker_host,), name='synchro_' + docker_host.name, daemon=True)
            th.start()
            self.host_checkers.append((th, docker_host))

        self.start()

    def _host_subthread(self, host_config: DockerHostConfig):
        log.info("Synchro thread for host {} started".format(host_config.name))

        self.host_stats[host_config.name] = NodeStats(host_config.name)

        while True:
            time_start = time.time()
            try:
                my_engine = DockerClient(host_config)
                container_list = my_engine.list(only_label={'zoe_deployment_name': get_conf().deployment_name})
                info = my_engine.info()
            except ZoeException as e:
                self.host_stats[host_config.name].status = 'offline'
                log.error(str(e))
                log.info('Node {} is offline'.format(host_config.name))
            else:
                if self.host_stats[host_config.name].status == 'offline':
                    log.info('Node {} is now online'.format(host_config.name))
                    self.host_stats[host_config.name].status = 'online'

                self.host_stats[host_config.name].container_count = info['Containers']
                self.host_stats[host_config.name].cores_total = info['NCPU']
                self.host_stats[host_config.name].memory_total = info['MemTotal']
                self.host_stats[host_config.name].labels = host_config.labels
                if info['Labels'] is not None:
                    self.host_stats[host_config.name].labels.union(set(info['Labels']))

                self.host_stats[host_config.name].memory_allocated = sum([cont['memory_soft_limit'] for cont in container_list if cont['memory_soft_limit'] != info['MemTotal']])
                self.host_stats[host_config.name].cores_allocated = sum([cont['cpu_quota'] / cont['cpu_period'] for cont in container_list if cont['cpu_period'] != 0])

                stats = {}
                self.host_stats[host_config.name].memory_reserved = 0
                self.host_stats[host_config.name].cores_reserved = 0
                for cont in container_list:
                    service = self.state.services.select(only_one=True, backend_host=host_config.name, backend_id=cont['id'])
                    if service is None:
                        log.warning('Container {} on host {} has no corresponding service'.format(cont['name'], host_config.name))
                        if cont['state'] == Service.BACKEND_DIE_STATUS:
                            log.warning('Terminating dead and orphan container {}'.format(cont['name']))
                            my_engine.terminate_container(cont['id'], delete=True)
                        continue
                    if service.status == service.TERMINATING_STATUS:
                        if service.backend_id is not None:
                            my_engine.terminate_container(service.backend_id, delete=True)
                        else:
                            service.set_inactive()

                    self._update_service_status(service, cont)
                    self.host_stats[host_config.name].memory_reserved += service.resource_reservation.memory.min
                    self.host_stats[host_config.name].cores_reserved += service.resource_reservation.cores.min
                    stats[service.id] = {
                        'core_limit': cont['cpu_quota'] / cont['cpu_period'],
                        'mem_limit': cont['memory_soft_limit']
                    }
                self.host_stats[host_config.name].service_stats = stats

                self.host_stats[host_config.name].images = []
                for dk_image in my_engine.list_images():
                    image = {
                        'id': dk_image.attrs['Id'],
                        'size': dk_image.attrs['Size'],
                        'names': dk_image.tags  # type: list
                    }
                    for name in image['names']:
                        if name[-7:] == ':latest':  # add an image with the name without 'latest' to fake Docker image lookup algorithm
                            image['names'].append(name[:-7])
                            break
                    self.host_stats[host_config.name].images.append(image)

            sleep_time = CHECK_INTERVAL - (time.time() - time_start)
            if sleep_time <= 0:
                log.warning('synchro thread for host {} is late by {:.2f} seconds'.format(host_config.name, sleep_time * -1))
                sleep_time = 0
            if self.stop.wait(timeout=sleep_time):
                break

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
