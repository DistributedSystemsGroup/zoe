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
from copy import deepcopy

from zoe_lib.config import get_conf
from zoe_lib.state import SQLManager, Service
from zoe_master.backends.docker.api_client import DockerClient
from zoe_master.backends.docker.config import DockerConfig, DockerHostConfig  # pylint: disable=unused-import
from zoe_master.exceptions import ZoeException
from zoe_master.stats import ClusterStats, NodeStats

log = logging.getLogger(__name__)

CHECK_INTERVAL = 10
THREAD_POOL_SIZE = 10


class DockerStateSynchronizer(threading.Thread):
    """The Docker Checker."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('checker')
        self.stop = False
        self.my_stop = False
        self.state = state
        self.setDaemon(True)
        self._platform_stats = ClusterStats()
        self.host_checkers = []
        for docker_host in DockerConfig(get_conf().backend_docker_config_file).read_config():
            th = threading.Thread(target=self._host_subthread, args=(docker_host,), name='synchro_' + docker_host.name, daemon=True)
            th.start()
            self.host_checkers.append((th, docker_host))

        self.start()

    def _host_subthread(self, host_config: DockerHostConfig):
        log.info("Checker thread started")
        node_stats = None
        for node in self._platform_stats.nodes:
            if node.name == host_config.name:
                node_stats = node
                break
        if node_stats is None:
            node_stats = NodeStats(host_config.name)
            self._platform_stats.nodes.append(node_stats)

        while not self.stop:
            try:
                my_engine = DockerClient(host_config)
            except ZoeException as e:
                log.error(str(e))
                node_stats.status = 'offline'
                log.info('Node {} is offline'.format(host_config.name))
                time.sleep(CHECK_INTERVAL)
                continue
            if node_stats.status == 'offline':
                log.info('Node {} is back online'.format(host_config.name))
            node_stats.status = 'online'
            node_stats.labels = host_config.labels

            service_list = self.state.service_list(backend_host=host_config.name)
            try:
                container_list = my_engine.list(only_label={'zoe_deployment_name': get_conf().deployment_name})
            except ZoeException:
                continue
            containers = {}
            for cont in container_list:
                containers[cont['id']] = cont

            services = {}
            for service in service_list:
                services[service.backend_id] = service

            for service in service_list:
                assert isinstance(service, Service)
                if service.backend_id in containers:
                    self._update_service_status(service, containers[service.backend_id], host_config)
                else:
                    if service.backend_status == service.BACKEND_DESTROY_STATUS:
                        continue
                    else:
                        service.set_backend_status(service.BACKEND_DESTROY_STATUS)

            try:
                self._update_node_stats(my_engine, node_stats)
            except ZoeException as e:
                log.error(str(e))
                node_stats.status = 'offline'
                log.warning('Node {} is offline'.format(host_config.name))

            time.sleep(CHECK_INTERVAL)

    def _update_node_stats(self, my_engine, node_stats: NodeStats):
        try:
            container_list = my_engine.list()
            info = my_engine.info()
        except ZoeException:
            return

        node_stats.container_count = info['Containers']
        node_stats.cores_total = info['NCPU']
        node_stats.memory_total = info['MemTotal']
        if info['Labels'] is not None:
            node_stats.labels += set(info['Labels'])

        stats = {}
        for cont in container_list:
            stats[cont['id']] = my_engine.stats(cont['id'], stream=False)

        node_stats.memory_reserved = sum([cont['memory_soft_limit'] for cont in container_list if cont['memory_soft_limit'] != node_stats.memory_total])
        node_stats.memory_in_use = sum([stat['memory_stats']['usage'] for stat in stats.values() if 'usage' in stat['memory_stats']])

        node_stats.cores_reserved = sum([cont['cpu_quota'] / cont['cpu_period'] for cont in container_list if cont['cpu_period'] != 0])

        node_stats.cores_in_use = sum([self._get_core_usage(stat) for stat in stats.values()])

        if get_conf().backend_image_management:
            for dk_image in my_engine.list_images():
                image = {
                    'id': dk_image.attrs['Id'],
                    'size': dk_image.attrs['Size'],
                    'names': dk_image.tags
                }
                for name in image['names']:
                    if name[-7:] == ':latest':  # add an image with the name without 'latest' to fake Docker image lookup algorithm
                        image['names'].append(name[:-7])
                        break
                node_stats.image_list.append(image)

    def _get_core_usage(self, stat):
        cpu_time_now = stat['cpu_stats']['cpu_usage']['total_usage']
        cpu_time_pre = stat['precpu_stats']['cpu_usage']['total_usage']
        return (cpu_time_now - cpu_time_pre) / 1000000000

    def _update_service_status(self, service: Service, container, host_config: DockerHostConfig):
        """Update the service status."""
        if service.backend_status != container['state']:
            old_status = service.backend_status
            service.set_backend_status(container['state'])
            log.debug('Updated service status, {} from {} to {}'.format(service.name, old_status, container['state']))
        for port in service.ports:
            if port.internal_name in container['ports'] and container['ports'][port.internal_name] is not None:
                port.activate(host_config.external_address, container['ports'][port.internal_name])
            else:
                port.reset()

    def run(self):
        """The thread loop."""
        log.info("Checker thread started")
        while not self.my_stop:
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
            time.sleep(CHECK_INTERVAL)

    def quit(self):
        """Stops the thread."""
        self.stop = True
        for th, conf_ in self.host_checkers:
            th.join()
        self.my_stop = True

    def get_platform_stats(self):
        """Returns a copy of the platform stats."""
        return deepcopy(self._platform_stats)
