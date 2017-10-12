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

from zoe_lib.state import Service
from zoe_lib.config import get_conf
from zoe_master.exceptions import ZoeStartExecutionRetryException, ZoeStartExecutionFatalException, ZoeException, ZoeNotEnoughResourcesException
import zoe_master.backends.base
from zoe_master.backends.service_instance import ServiceInstance
from zoe_master.backends.docker.threads import DockerStateSynchronizer
from zoe_master.backends.docker.api_client import DockerClient
from zoe_master.backends.docker.config import DockerConfig, DockerHostConfig  # pylint: disable=unused-import
from zoe_master.stats import ClusterStats  # pylint: disable=unused-import

log = logging.getLogger(__name__)

# These two module-level variables hold the references to the monitor and checker threads
_checker = None


class DockerEngineBackend(zoe_master.backends.base.BaseBackend):
    """Zoe backend implementation for old-style stand-alone Docker Swarm."""
    def __init__(self, opts):
        super().__init__(opts)
        self.docker_config = DockerConfig(get_conf().backend_docker_config_file).read_config()

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
        engine.terminate_container(service.backend_id, delete=True)
        service.set_backend_status(service.BACKEND_DESTROY_STATUS)

    def platform_state(self) -> ClusterStats:
        """Get the platform state."""
        return _checker.get_platform_stats()

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
