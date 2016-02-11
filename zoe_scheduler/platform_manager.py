# Copyright (c) 2015, Daniele Venzano
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

import logging

from zoe_lib.swarm_client import SwarmClient, ContainerOptions

from zoe_lib.exceptions import ZoeException
from zoe_scheduler.config import get_conf
from zoe_scheduler.scheduler import ZoeScheduler
from zoe_scheduler.state import execution as execution_module, application as application_module, container as container_module
from zoe_scheduler.state.manager import StateManager
from zoe_scheduler.stats import ContainerStats
from zoe_scheduler.stats import SwarmStats, SchedulerStats

log = logging.getLogger(__name__)


class PlatformManager:
    """
    :type swarm: SwarmClient
    :type scheduler: ZoeScheduler
    :type state_manager: StateManager
    """
    def __init__(self, sched_policy_class):
        self.swarm = SwarmClient(get_conf())
        self.scheduler = ZoeScheduler(self, sched_policy_class)
        self.state_manager = None

    def execution_submitted(self, execution: execution_module.Execution):
        execution.set_scheduled()
        self.scheduler.incoming(execution)

    def execution_start(self, execution: execution_module.Execution) -> bool:
        try:
            self._application_to_containers(execution)
        except ZoeException:
            self.execution_terminate(execution, reason='error')
            raise
        execution.set_started()
        self.state_manager.state_updated()

    def _application_to_containers(self, execution: execution_module.Execution):
        for process in execution.application.processes:
            self._spawn_process(execution, process)

    def _spawn_process(self, execution: execution_module.Execution, process_description: application_module.Process) -> bool:
        copts = ContainerOptions()
        copts.name = process_description.name + "-{}".format(execution.id)
        copts.set_memory_limit(process_description.required_resources['memory'])
        copts.network_name = 'zoe-usernet-{}'.format(execution.owner.id)
        container_id = self.state_manager.gen_id()
        copts.labels = {
            'zoe': '',
            'zoe.execution_id': str(execution.id),
            'zoe.container_id': str(container_id)
        }
        if process_description.monitor:
            copts.labels['zoe.monitor'] = ''
        else:
            copts.labels['zoe.normal'] = ''
        copts.restart = not process_description.monitor  # Monitor containers should not restart

        # Generate a dictionary containing the current cluster status (before the new container is spawned)
        # This information is used to substitute template strings in the environment variables
        subst_dict = {
            "execution_id": str(execution.id),
            "user_id": str(execution.owner.id),
            'user_name': execution.owner.name
        }
        for env_name, env_value in process_description.environment:
            try:
                env_value = env_value.format(**subst_dict)
            except KeyError:
                raise ZoeException("cannot find variable to substitute in expression {}".format(env_value))
            copts.add_env_variable(env_name, env_value)

        # The same dictionary is used for templates in the command
        if process_description.command is not None:
            copts.set_command(process_description.command.format(**subst_dict))

        cont_info = self.swarm.spawn_container(process_description.docker_image, copts)
        container = container_module.Container(self.state_manager)
        container.docker_id = cont_info["docker_id"]
        container.ip_address = cont_info["ip_address"]
        container.name = copts.name
        container.is_monitor = process_description.monitor
        container.ports = [p.to_dict() for p in process_description.ports]

        container.id = container_id
        execution.containers.append(container)
        container.execution = execution

        self.swarm.connect_to_network(container.docker_id, 'eeef9754c16790a29d5210c5d9ad8e66614ee8a6229b6dc6f779019d46cec792')

        self.state_manager.new('container', container)
        return True

    def execution_terminate(self, execution: execution_module.Execution, reason):
        """
        :param execution: The execution to be terminated
        :param reason: termination reason
        :return:
        """
        logs = []
        if len(execution.containers) > 0:
            for c in execution.containers:
                assert isinstance(c, container_module.Container)
                l = self.log_get(c.id)
                if l is not None:
                    logs.append((c.name, l))
                self.swarm.terminate_container(c.docker_id, delete=True)
                self.state_manager.delete('container', c.id)
            execution.store_logs(logs)

        if reason == 'error':
            execution.set_error()
        elif reason == 'finished':
            execution.set_finished()
        else:
            execution.set_terminated()
        self.scheduler.execution_terminate(execution)

    def start_gateway_container(self, user):
        copts = ContainerOptions()
        copts.name = 'gateway-{}'.format(user.id)
        copts.network_name = 'zoe-usernet-{}'.format(user.id)
        copts.ports.append(1080)
        copts.labels = ['zoe.gateway']
        copts.restart = True
        if user.role == 'guest':
            image = get_conf().private_registry + '/zoerepo/guest-gateway'
        else:
            image = get_conf().private_registry + '/zoerepo/guest-gateway'  # TODO: create an image with ssh
        cont_info = self.swarm.spawn_container(image, copts)
        if cont_info is None:
            raise ZoeException('Cannot create user gateway container')
        user.gateway_docker_id = cont_info['docker_id']
        user.set_gateway_urls(cont_info)
        self.swarm.connect_to_network(user.gateway_docker_id, 'eeef9754c16790a29d5210c5d9ad8e66614ee8a6229b6dc6f779019d46cec792')

    def kill_gateway_container(self, user):
        self.swarm.terminate_container(user.gateway_docker_id, delete=True)
        user.gateway_docker_id = None
        user.gateway_urls = []

    def create_user_network(self, user):
        log.info('Creating a new network for user {}'.format(user.id))
        net_name = 'zoe-usernet-{}'.format(user.id)
        net_id = self.swarm.network_create(net_name)
        user.network_id = net_id

    def remove_user_network(self, user):
        log.info('Removing network for user {}'.format(user.name))
        self.swarm.network_remove(user.network_id)

    def log_get(self, container_id: int) -> str:
        container = self.state_manager.get_one('container', id=container_id)
        if container is None:
            return ''
        else:
            return self.swarm.log_get(container.docker_id)

    def container_stats(self, container_id: int) -> ContainerStats:
        container = self.state_manager.get_one('container', id=container_id)
        return self.swarm.stats(container.docker_id)

    def is_container_alive(self, container: container_module.Container) -> bool:
        ret = self.swarm.inspect_container(container.docker_id)
        if ret is None:
            return False
        return ret["running"]

    def swarm_stats(self) -> SwarmStats:
        # TODO implement some caching
        return self.swarm.info()

    def scheduler_stats(self) -> SchedulerStats:
        return self.scheduler.scheduler_policy.stats()

    def check_state_swarm_consistency(self):
        state_changed = False
        users = self.state_manager.get('user')
        networks = self.swarm.network_list()
        gateways = self.swarm.list(['zoe.gateway'])

        users_no_network = []
        users_no_gateway = []
        networks_to_delete = []
        gateways_to_delete = []

        for u in users:
            if u.network_id is None:
                log.error('state inconsistency: user {} has no network')
                users_no_network.append(u)
            elif u.network_id not in [x['id'] for x in networks]:
                log.error('state inconsistency: user {} has an invalid network')
                u.network_id = None
                users_no_network.append(u)

            if u.gateway_docker_id is None:
                log.error('state inconsistency: user {} has no gateway')
                users_no_gateway.append(u)
            elif u.gateway_docker_id not in [x['id'] for x in gateways]:
                log.error('state inconsistency: user {} has an invalid gateway container ID')
                u.gateway_docker_id = None
                users_no_gateway.append(u)

        duplicate_check = set()
        for n in networks:
            try:
                uid = int(n['name'][len('zoe-usernet-'):])
            except ValueError:
                log.error('network {} does not belong to Zoe, bug?'.format(n['name']))
                networks_to_delete.append(n['id'])
                continue
            if uid in duplicate_check:
                log.warning('state inconsistency: found two networks for the same user')
                networks_to_delete.append(n['id'])
                continue
            duplicate_check.add(uid)
            user = self.state_manager.get_one('user', id=uid)
            if user is not None and user in users_no_network:
                user.network_id = n['id']
                users_no_network.remove(user)
                log.error('fixed: user {} linked to network {}'.format(user.name, n['name']))
                state_changed = True
                continue
            elif user is None:
                log.error('state inconsistency: found a network for user {} who no longer exists'.format(uid))
                networks_to_delete.append(n['id'])

        for g in gateways:
            try:
                uid = int(g['name'][len('gateway-'):])
            except ValueError:
                log.error('container {} does not belong to Zoe, bug?'.format(g['name']))
                gateways_to_delete.append(g['id'])
                continue
            user = self.state_manager.get_one('user', id=uid)
            if user is not None and user in users_no_gateway:
                user.gateway_docker_id = g['id']
                users_no_gateway.remove(user)
                cont_info = self.swarm.inspect_container(g['id'])
                user.set_gateway_urls(cont_info)
                log.error('fixed: user {} linked to gateway {}'.format(user.name, g['name']))
                state_changed = True
                continue
            elif user is None:
                log.error('state inconsistency: found a gateway for user {} who no longer exists'.format(uid))
                gateways_to_delete.append(g['id'])

        # Fix all inconsistencies found
        for g in gateways_to_delete:
            log.error('fixed: terminating orphan gateway container {}'.format(g[:8]))
            self.swarm.terminate_container(g, delete=True)
        for n in networks_to_delete:
            log.error('fixed: terminating orphan network {}'.format(n[:8]))
            self.swarm.network_remove(n)

        for u in users_no_network:
            log.error('fixed: creating network for user {}'.format(u.name))
            self.create_user_network(u)
        for u in users_no_gateway:
            log.error('fixed: creating gateway for user {}'.format(u.name))
            self.start_gateway_container(u)

        # ### Check executions and container consistency
        swarm_containers = self.swarm.list(only_label='zoe')
        conts_state_to_delete = []
        for c_id, c in self.state_manager.containers.items():
            if c.docker_id not in [x['id'] for x in swarm_containers]:
                log.error('fixed: removing from state container {} that does not exist in Swarm'.format(c.name))
                conts_state_to_delete.append(c_id)
        for c_id in conts_state_to_delete:
            self.state_manager.delete('container', c_id)

        if state_changed or len(users_no_gateway) > 0 or len(users_no_network) > 0:
            self.state_manager.state_updated()
