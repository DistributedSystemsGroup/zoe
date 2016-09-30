# Copyright (c) 2016, Daniele Venzano
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

"""Translates a ZApp description into Docker containers."""

import logging

from zoe_master.workspace.filesystem import ZoeFSWorkspace
from zoe_master.exceptions import ZoeStartExecutionRetryException, ZoeStartExecutionFatalException, ZoeException

from zoe_lib.config import get_conf
from zoe_lib.exceptions import ZoeLibException, ZoeNotEnoughResourcesException
from zoe_lib.sql_manager import Execution, Service
from zoe_lib.swarm_client import DockerContainerOptions, SwarmClient

log = logging.getLogger(__name__)


def execution_to_containers(execution: Execution) -> None:
    """Translate an execution object into containers.

    If an error occurs some containers may have been created and needs to be cleaned-up.
    In case of error exceptions are raised.
    """
    ordered_service_list = sorted(execution.services, key=lambda x: x.description['startup_order'])

    env_subst_dict = {
        'execution_id': execution.id,
        "execution_name": execution.name,
        'user_name': execution.user_id,
        'deployment_name': get_conf().deployment_name,
    }

    for service in ordered_service_list:
        env_subst_dict['dns_name#' + service.name] = service.dns_name

    for service in ordered_service_list:
        env_subst_dict['dns_name#self'] = service.dns_name
        service.set_starting()
        _spawn_service(execution, service, env_subst_dict)


def _gen_environment(service, env_subst_dict, copts):
    """ Generate a dictionary containing the current cluster status (before the new container is spawned)

    This information is used to substitute template strings in the environment variables."""
    for env_name, env_value in service.description['environment']:
        try:
            env_value = env_value.format(**env_subst_dict)
        except KeyError:
            error_msg = "Unknown variable in environment expression '{}', known variables are: {}".format(env_value, list(env_subst_dict.keys()))
            service.set_error(error_msg)
            raise ZoeStartExecutionFatalException("Service {} has wrong environment expression")
        copts.add_env_variable(env_name, env_value)


def _spawn_service(execution: Execution, service: Service, env_subst_dict: dict):
    copts = DockerContainerOptions()
    copts.gelf_log_address = get_conf().gelf_address
    copts.name = service.dns_name
    copts.set_memory_limit(service.description['required_resources']['memory'])
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
    if service.description['monitor']:
        copts.labels['zoe.monitor'] = 'true'
    else:
        copts.labels['zoe.monitor'] = 'false'
    copts.restart = not service.description['monitor']  # Monitor containers should not restart

    _gen_environment(service, env_subst_dict, copts)

    for port in service.description['ports']:
        if 'expose' in port and port['expose']:
            copts.ports.append(port['port_number'])  # FIXME UDP ports?

    if 'volumes' in service.description:
        for path, mount_point, readonly in service.description['volumes']:
            copts.add_volume_bind(path, mount_point, readonly)

    if 'constraints' in service.description:
        for constraint in service.description['constraints']:
            copts.add_constraint(constraint)

    fswk = ZoeFSWorkspace()
    if fswk.can_be_attached():
        copts.add_volume_bind(fswk.get_path(execution.user_id), fswk.get_mountpoint(), False)
        copts.add_env_variable('ZOE_WORKSPACE', fswk.get_mountpoint())

    # The same dictionary is used for templates in the command
    if 'command' in service.description:
        copts.set_command(service.description['command'].format(**env_subst_dict))

    try:
        swarm = SwarmClient(get_conf())
    except Exception as e:
        raise ZoeStartExecutionFatalException(str(e))

    try:
        cont_info = swarm.spawn_container(service.description['docker_image'], copts)
    except ZoeNotEnoughResourcesException:
        service.set_error('Not enough free resources to satisfy reservation request')
        raise ZoeStartExecutionRetryException('Not enough free resources to satisfy reservation request for service {}'.format(service.name))
    except (ZoeException, ZoeLibException) as e:
        raise ZoeStartExecutionFatalException(str(e))

    service.set_active(cont_info["docker_id"])

    if 'networks' in service.description:
        for net in service.description['networks']:
            try:
                swarm.connect_to_network(service.docker_id, net)
            except ZoeException as e:
                service.set_error(str(e))
                raise ZoeStartExecutionFatalException("Failed to attach network {} to service {}".format(net, service.name))

    return


def terminate_execution(execution: Execution) -> None:
    """Terminate an execution, making sure no containers are left in Swarm."""
    execution.set_cleaning_up()
    swarm = SwarmClient(get_conf())
    for service in execution.services:
        assert isinstance(service, Service)
        if service.docker_id is not None:
            service.set_terminating()
            swarm.terminate_container(service.docker_id, delete=True)
            service.set_inactive()
            log.debug('Service {} terminated'.format(service.name))
    execution.set_terminated()
