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

"""Zoe backend implementation for one or more Docker Engines."""

import logging
import re
import time
import threading

from zoe_lib.state import Service
from zoe_lib.config import get_conf
from zoe_master.exceptions import ZoeStartExecutionRetryException, ZoeStartExecutionFatalException, ZoeException, ZoeNotEnoughResourcesException
import zoe_master.backends.base
from zoe_master.backends.service_instance import ServiceInstance
from zoe_master.backends.docker.threads import DockerStateSynchronizer
from zoe_master.backends.docker.api_client import DockerClient
from zoe_master.backends.docker.config import DockerConfig, DockerHostConfig  # pylint: disable=unused-import
from zoe_master.stats import ClusterStats, NodeStats
from zoe_master.metrics.incoming.kairosdb import KairosDBInMetrics

log = logging.getLogger(__name__)

# These two module-level variables hold the references to the monitor and checker threads
_checker = None


class DockerEngineBackend(zoe_master.backends.base.BaseBackend):
    """Zoe backend implementation for old-style stand-alone Docker Swarm."""
    def __init__(self, opts):
        super().__init__(opts)
        self.docker_config = DockerConfig(get_conf().backend_docker_config_file).read_config()
        self.cached_stats = None

    def _get_config(self, host) -> DockerHostConfig:
        for conf in self.docker_config:
            if conf.name == host:
                return conf

    @classmethod
    def init(cls, state):
        """Initializes Swarm backend starting the event monitoring thread."""
        global _checker
        _checker = DockerStateSynchronizer(state)

    @classmethod
    def shutdown(cls):
        """Performs a clean shutdown of the resources used by Swarm backend."""
        _checker.quit()

    def spawn_service(self, service_instance: ServiceInstance):
        """Spawn a service, translating a Zoe Service into a Docker container."""
        parsed_name = re.search(r'^(?:([^\/]+)\/)?(?:([^\/]+)\/)?([^@:\/]+)(?:[@:](.+))?$', service_instance.image_name)
        if parsed_name.group(4) is None:
            raise ZoeStartExecutionFatalException('Image {} does not have a version tag'.format(service_instance.image_name))
        conf = self._get_config(service_instance.backend_host)
        try:
            engine = DockerClient(conf)
            cont_info = engine.spawn_container(service_instance)
        except ZoeNotEnoughResourcesException:
            raise ZoeStartExecutionRetryException('Not enough free resources to satisfy reservation request for service {}'.format(service_instance.name))
        except ZoeException as e:
            raise ZoeStartExecutionFatalException(str(e))

        return cont_info["id"], cont_info['external_address'], cont_info['ports']

    def terminate_service(self, service: Service) -> None:
        """Terminate and delete a container."""
        conf = self._get_config(service.backend_host)
        engine = DockerClient(conf)
        if service.backend_id is not None:
            engine.terminate_container(service.backend_id, delete=True)
        else:
            log.error('Cannot terminate service {}, since it has not backend ID'.format(service.name))
        service.set_backend_status(service.BACKEND_DESTROY_STATUS)

    def platform_state(self, state=None) -> ClusterStats:
        """Get the platform state."""
        time_start = time.time()
        platform_stats = ClusterStats()
        th_list = []
        for host_conf in self.docker_config:  # type: DockerHostConfig
            node_stats = NodeStats(host_conf.name)

            th = threading.Thread(target=self._update_node_stats, args=(host_conf, node_stats, state), name='stats_host_{}'.format(host_conf.name), daemon=True)
            th.start()
            th_list.append((th, node_stats))

        for th, node_stats in th_list:
            th.join()
            platform_stats.nodes.append(node_stats)

        log.debug('Time for platform stats: {:.2f}s'.format(time.time() - time_start))
        return platform_stats

    def _update_node_stats(self, host_conf: DockerHostConfig, node_stats: NodeStats, state):
        node_stats.labels = host_conf.labels
        try:
            my_engine = DockerClient(host_conf)
        except ZoeException as e:
            log.error(str(e))
            node_stats.status = 'offline'
            log.info('Node {} is offline'.format(host_conf.name))
            return
        else:
            node_stats.status = 'online'

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

        node_stats.memory_reserved = sum([cont['memory_soft_limit'] for cont in container_list if cont['memory_soft_limit'] != node_stats.memory_total])
        node_stats.cores_reserved = sum([cont['cpu_quota'] / cont['cpu_period'] for cont in container_list if cont['cpu_period'] != 0])

        stats = {}
        if get_conf().kairosdb_enable:
            kdb = KairosDBInMetrics()
            for cont in container_list:
                stats[cont['id']] = kdb.get_service_usage(cont['name'])
            stats[cont['id']]['mem_limit'] = cont['memory_soft_limit']

            node_stats.memory_in_use = sum([stat['mem_usage'] for stat in stats.values()])
            node_stats.cores_in_use = sum([stat['cpu_usage'] for stat in stats.values()])
        else:
            for cont in container_list:
                try:
                    stats[cont['id']] = my_engine.stats(cont['id'], stream=False)
                except ZoeException:
                    continue

            node_stats.memory_in_use = sum([stat['memory_stats']['usage'] for stat in stats.values() if 'usage' in stat['memory_stats']])
            node_stats.cores_in_use = sum([self._get_core_usage(stat) for stat in stats.values()])
        node_stats.cont_stats = stats

        if get_conf().backend_image_management:
            node_stats.image_list = []
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

    def service_log(self, service: Service):
        """Get the log."""
        conf = self._get_config(service.backend_host)
        engine = DockerClient(conf)
        return engine.logs(service.backend_id, True, False)

    def preload_image(self, image_name):
        """Pull an image from a Docker registry into each host. We shuffle the list to prevent the scheduler to find always the first host in the list."""
        parsed_name = re.search(r'^(?:([^\/]+)\/)?(?:([^\/]+)\/)?([^@:\/]+)(?:[@:](.+))?$', image_name)
        if parsed_name.group(4) is None:
            raise ZoeException('Image {} does not have a version tag'.format(image_name))
        one_success = False
        for host_conf in self.docker_config:
            log.debug('Pre-loading image {} on host {}'.format(image_name, host_conf.name))
            time_start = time.time()
            my_engine = DockerClient(host_conf)
            try:
                my_engine.pull_image(image_name)
            except ZoeException:
                log.error('Image {} pre-loading failed on host {}'.format(image_name, host_conf.name))
                continue
            else:
                one_success = True
            log.debug('Image {} pre-loaded on host {} in {:.2f}s'.format(image_name, host_conf.name, time.time() - time_start))
        if not one_success:
            raise ZoeException('Cannot pull image {}'.format(image_name))

    def update_service(self, service, cores=None, memory=None):
        """Update a service reservation."""
        conf = self._get_config(service.backend_host)
        engine = DockerClient(conf)
        if service.backend_id is not None:
            info = engine.info()
            if cores is not None and cores > info['NCPU']:
                cores = info['NCPU']
            if memory is not None and memory > info['MemTotal']:
                memory = info['MemTotal']
            if cores is not None:
                cpu_quota = cores * 1000000
            else:
                cpu_quota = None
            engine.update(service.backend_id, cpu_quota=cpu_quota, mem_reservation=memory)
        else:
            log.error('Cannot terminate service {}, since it has not backend ID'.format(service.name))
