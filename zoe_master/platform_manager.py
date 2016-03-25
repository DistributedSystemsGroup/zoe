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

from zoe_lib.swarm_client import SwarmClient, DockerContainerOptions

from zoe_lib.exceptions import ZoeException
from zoe_master.config import get_conf, singletons
from zoe_master.scheduler import ZoeScheduler
from zoe_master.state import execution as execution_module, application as application_module, service as service_module, user as user_module
from zoe_master.state.manager import StateManager
from zoe_master.stats import SwarmStats, SchedulerStats
import zoe_master.workspace.base

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
        self.state_manager = singletons['state_manager']

    def execution_prepare(self, name: str, user: user_module.User, application_description: application_module.ApplicationDescription):
        ex = execution_module.Execution(self.state_manager)
        ex.user = user
        ex.name = name
        ex.application = application_description
        return ex

    def execution_submit(self, execution: execution_module.Execution):
        execution.id = self.state_manager.gen_id()
        self.state_manager.new('execution', execution)

        execution.set_scheduled()
        self.scheduler.incoming(execution)

        self.state_manager.state_updated()

    def execution_start(self, execution: execution_module.Execution) -> bool:
        try:
            self._application_to_containers(execution)
        except ZoeException as e:
            log.warning('Error starting application: {}'.format(e.value))
            self.execution_terminate(execution, reason='error')
            raise
        execution.set_started()
        self.state_manager.state_updated()

    def _application_to_containers(self, execution: execution_module.Execution):
        for service in execution.application.services:
            self._spawn_service(execution, service)

    def _spawn_service(self, execution: execution_module.Execution, service_description: application_module.ServiceDescription) -> bool:
        copts = DockerContainerOptions()
        copts.gelf_log_address = get_conf().gelf_address
        copts.name = service_description.name + "-" + execution.name + "-" + execution.owner.name + "-" + get_conf().deployment_name + "-zoe"
        copts.set_memory_limit(service_description.required_resources['memory'])
        copts.network_name = '{}-{}-zoe'.format(execution.owner.name, get_conf().deployment_name)
        service_id = self.state_manager.gen_id()
        copts.labels = {
            'zoe.execution.name': execution.name,
            'zoe.execution.id': str(execution.id),
            'zoe.service.name': service_description.name,
            'zoe.service.id': str(service_id),
            'zoe.owner': execution.owner.name,
            'zoe.deployment_name': get_conf().deployment_name,
            'zoe.type': 'app_service'
        }
        if service_description.monitor:
            copts.labels['zoe.monitor'] = 'true'
        else:
            copts.labels['zoe.monitor'] = 'false'
        copts.restart = not service_description.monitor  # Monitor containers should not restart

        # Generate a dictionary containing the current cluster status (before the new container is spawned)
        # This information is used to substitute template strings in the environment variables
        subst_dict = {
            "execution_name": execution.name,
            'user_name': execution.owner.name,
            'deployment_name': get_conf().deployment_name
        }
        for env_name, env_value in service_description.environment:
            try:
                env_value = env_value.format(**subst_dict)
            except KeyError:
                raise ZoeException("cannot find variable to substitute in expression {}".format(env_value))
            copts.add_env_variable(env_name, env_value)

        for path, mountpoint, readonly in service_description.volumes:
            copts.add_volume_bind(path, mountpoint, readonly)

        for wks in singletons['workspace_managers']:
            assert isinstance(wks, zoe_master.workspace.base.ZoeWorkspaceBase)
            if wks.can_be_attached():
                copts.add_volume_bind(wks.get_path(execution.owner), wks.get_mountpoint(), False)

        # The same dictionary is used for templates in the command
        if service_description.command is not None:
            copts.set_command(service_description.command.format(**subst_dict))

        cont_info = self.swarm.spawn_container(service_description.docker_image, copts)
        service = service_module.Service(self.state_manager)
        service.docker_id = cont_info["docker_id"]
        service.ip_address = cont_info["ip_address"]
        service.name = copts.name
        service.is_monitor = service_description.monitor
        service.ports = [p.to_dict() for p in service_description.ports]

        service.id = service_id
        execution.services.append(service)
        service.execution = execution

        for net in service_description.networks:
            self.swarm.connect_to_network(service.docker_id, net)

        self.state_manager.new('service', service)
        return True

    def execution_terminate(self, execution: execution_module.Execution, reason):
        """
        :param execution: The execution to be terminated
        :param reason: termination reason
        :return:
        """
        if len(execution.services) > 0:
            containers = execution.services.copy()
            for c in containers:
                assert isinstance(c, service_module.Service)
                self.swarm.terminate_container(c.docker_id, delete=True)
                self.state_manager.delete('service', c.id)
                log.info('Service {} terminated'.format(c.name))

        if reason == 'error':
            execution.set_error()
            return
        elif reason == 'finished':
            execution.set_finished()
        else:
            execution.set_terminated()
        self.scheduler.execution_terminate(execution)

    def start_gateway_container(self, user):
        copts = DockerContainerOptions()
        copts.name = 'gateway-{}-{}-zoe'.format(user.name, get_conf().deployment_name)
        copts.network_name = '{}-{}-zoe'.format(user.name, get_conf().deployment_name)
        copts.ports.append(1080)
        copts.labels = {
            'zoe.owner': user.name,
            'zoe.deployment': get_conf().deployment_name,
            'zoe.type': 'gateway'
        }
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

    def kill_gateway_container(self, user):
        self.swarm.terminate_container(user.gateway_docker_id, delete=True)
        user.gateway_docker_id = None
        user.gateway_urls = []

    def create_user_network(self, user):
        log.info('Creating a new network for user {}'.format(user.id))
        net_name = '{}-{}-zoe'.format(user.name, get_conf().deployment_name)
        net_id = self.swarm.network_create(net_name)
        user.network_id = net_id

    def remove_user_network(self, user):
        log.info('Removing network for user {}'.format(user.name))
        self.swarm.network_remove(user.network_id)

    def is_service_alive(self, service: service_module.Service) -> bool:
        ret = self.swarm.inspect_container(service.docker_id)
        if ret is None:
            return False
        return ret["running"]

    def swarm_stats(self) -> SwarmStats:
        return singletons['stats_manager'].swarm_stats()

    def scheduler_stats(self) -> SchedulerStats:
        return self.scheduler.scheduler_policy.stats()

    def check_workspaces(self):
        users = self.state_manager.get('user')
        for user in users:
            for wks in singletons['workspace_managers']:
                assert isinstance(wks, zoe_master.workspace.base.ZoeWorkspaceBase)
                if not wks.exists(user):
                    log.warning('workspace for user {} not found, creating...'.format(user.name))
                    wks.create(user)

    def check_state_swarm_consistency(self):
        state_changed = False
        users = self.state_manager.get('user')
        networks = self.swarm.network_list('{}-zoe'.format(get_conf().deployment_name))
        gateways = self.swarm.list({'zoe.type': 'gateway', 'zoe.deployment': get_conf().deployment_name})

        users_no_network = []
        users_no_gateway = []
        networks_to_delete = []
        gateways_to_delete = []

        for u in users:
            if u.network_id is None:
                log.error('state inconsistency: user {} has no network'.format(u.name))
                users_no_network.append(u)
            elif u.network_id not in [x['id'] for x in networks]:
                log.error('state inconsistency: user {} has an invalid network'.format(u.name))
                u.network_id = None
                users_no_network.append(u)

            if u.gateway_docker_id is None:
                log.error('state inconsistency: user {} has no gateway'.format(u.name))
                users_no_gateway.append(u)
            elif u.gateway_docker_id not in [x['id'] for x in gateways]:
                log.error('state inconsistency: user {} has an invalid gateway container ID'.format(u.name))
                u.gateway_docker_id = None
                users_no_gateway.append(u)

        duplicate_check = set()
        for n in networks:
            try:
                username = n['name'].split('-')[0]
            except ValueError:
                log.error('network {} does not belong to Zoe, bug?'.format(n['name']))
                networks_to_delete.append(n['id'])
                continue
            if username in duplicate_check:
                log.warning('state inconsistency: found two networks for the same user')
                networks_to_delete.append(n['id'])
                continue
            duplicate_check.add(username)
            user = self.state_manager.get_one('user', name=username)
            if user is not None and user in users_no_network:
                user.network_id = n['id']
                users_no_network.remove(user)
                log.error('fixed: user {} linked to network {}'.format(user.name, n['name']))
                state_changed = True
                continue
            elif user is None:
                log.error('state inconsistency: found a network for user {} who no longer exists'.format(username))
                networks_to_delete.append(n['id'])

        for g in gateways:
            try:
                username = g['name'].split('-')[1]
            except ValueError:
                log.error('container {} does not belong to Zoe, bug?'.format(g['name']))
                gateways_to_delete.append(g['id'])
                continue
            user = self.state_manager.get_one('user', name=username)
            if user is not None and user in users_no_gateway:
                user.gateway_docker_id = g['id']
                users_no_gateway.remove(user)
                cont_info = self.swarm.inspect_container(g['id'])
                user.set_gateway_urls(cont_info)
                log.error('fixed: user {} linked to gateway {}'.format(user.name, g['name']))
                state_changed = True
                continue
            elif user is None:
                log.error('state inconsistency: found a gateway for user {} who no longer exists'.format(username))
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
        swarm_containers = self.swarm.list(only_label={'zoe.deployment_name': get_conf().deployment_name})
        conts_state_to_delete = []
        for c_id, c in self.state_manager.services.items():
            if c.docker_id not in [x['id'] for x in swarm_containers]:
                log.error('fixed: removing from state container {} that does not exist in Swarm'.format(c.name))
                conts_state_to_delete.append(c_id)
        for c_id in conts_state_to_delete:
            self.state_manager.delete('service', c_id)

        if state_changed or len(users_no_gateway) > 0 or len(users_no_network) > 0:
            self.state_manager.state_updated()
