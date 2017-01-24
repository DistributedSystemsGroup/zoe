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

"""Zoe backend implementation for old-style stand-alone Docker Swarm."""

import logging
from typing import Dict

from zoe_lib.config import get_conf
from zoe_lib.exceptions import ZoeLibException, ZoeNotEnoughResourcesException
from zoe_lib.state import Execution, Service
from zoe_master.backends.old_swarm.api_client import DockerContainerOptions, SwarmClient
from zoe_master.exceptions import ZoeStartExecutionRetryException, ZoeStartExecutionFatalException, ZoeException
from zoe_master.workspace.filesystem import ZoeFSWorkspace
import zoe_master.backends.common
import zoe_master.backends.base
from zoe_master.backends.old_swarm.threads import SwarmMonitor, SwarmStateSynchronizer
from zoe_master.stats import NodeStats, ClusterStats  # pylint: disable=unused-import

log = logging.getLogger(__name__)

# These two module-level variables hold the references to the monitor and checker threads
_monitor = None
_checker = None


class OldSwarmBackend(zoe_master.backends.base.BaseBackend):
    """Zoe backend implementation for old-style stand-alone Docker Swarm."""
    def __init__(self, opts):
        super().__init__(opts)
        self.swarm = SwarmClient(opts)

    @classmethod
    def init(cls, state):
        """Initializes Swarm backend starting the event monitoring thread."""
        global _monitor, _checker
        _monitor = SwarmMonitor(state)
        _checker = SwarmStateSynchronizer(state)

    @classmethod
    def shutdown(cls):
        """Performs a clean shutdown of the resources used by Swarm backend."""
        _monitor.quit()
        _checker.quit()

    def spawn_service(self, execution: Execution, service: Service, env_subst_dict: Dict):
        """Spawn a service, translating a Zoe Service into a Docker container."""
        copts = DockerContainerOptions()
        copts.gelf_log_address = get_conf().gelf_address
        copts.name = service.dns_name
        copts.set_memory_limit(service.resource_reservation.memory)
        copts.network_name = get_conf().overlay_network_name
        copts.labels = {
            'zoe.execution.name': execution.name,
            'zoe.execution.id': str(execution.id),
            'zoe.service.name': service.name,
            'zoe.service.id': str(service.id),
            'zoe.owner': execution.user_id,
            'zoe.deployment_name': get_conf().deployment_name,
            'zoe.type': 'app_service'
        }
        if service.is_monitor:
            copts.labels['zoe.monitor'] = 'true'
        else:
            copts.labels['zoe.monitor'] = 'false'

        # Always disable autorestart
        # if 'disable_autorestart' in execution.description and execution.description['disable_autorestart']:
        #     log.debug("Autorestart disabled for service {}".format(service.id))
        #     copts.restart = False
        # else:
        # copts.restart = not service.is_monitor  # Monitor containers should not restart
        copts.restart = False

        env_vars = zoe_master.backends.common.gen_environment(service, env_subst_dict)
        for name, value in env_vars:
            copts.add_env_variable(name, value)

        for port in service.ports:
            if port.expose:
                copts.ports.append(port.port_number)

        for volume in service.volumes:
            if volume.type == "host_directory":
                copts.add_volume_bind(volume.path, volume.mount_point, volume.readonly)
            else:
                log.warning('Docker Swarm backend does not support volume type {}'.format(volume.type))

        # if 'constraints' in service.description:
        #     for constraint in service.description['constraints']:
        #         copts.add_constraint(constraint)

        fswk = ZoeFSWorkspace()
        if fswk.can_be_attached():
            copts.add_volume_bind(fswk.get_path(execution.user_id), fswk.get_mountpoint(), False)
            copts.add_env_variable('ZOE_WORKSPACE', fswk.get_mountpoint())

        # The same dictionary is used for templates in the command
        copts.set_command(service.command.format(**env_subst_dict))

        try:
            cont_info = self.swarm.spawn_container(service.image_name, copts)
        except ZoeNotEnoughResourcesException:
            service.set_error('Not enough free resources to satisfy reservation request')
            raise ZoeStartExecutionRetryException('Not enough free resources to satisfy reservation request for service {}'.format(service.name))
        except (ZoeException, ZoeLibException) as e:
            raise ZoeStartExecutionFatalException(str(e))

        service.set_active(cont_info["docker_id"], cont_info['ip_address'][get_conf().overlay_network_name])

    def terminate_service(self, service: Service) -> None:
        """Terminate and delete a container."""
        self.swarm.terminate_container(service.backend_id, delete=True)

    def platform_state(self) -> ClusterStats:
        """Get the platform state."""
        info = self.swarm.info()
        for node in info.nodes:  # type: NodeStats
            node.memory_free = node.memory_total - node.memory_reserved
            node.cores_free = node.cores_total - node.cores_reserved
        return info
