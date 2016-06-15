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
            self.execution_terminate(execution, reason='error', message=e.value)
            raise
        execution.set_started()
        self.state_manager.state_updated()

    def _application_to_containers(self, execution: execution_module.Execution):
        ordered_service_list = sorted(execution.application.services, key=lambda x: x.startup_order)
        for service in ordered_service_list:
            for counter in range(service.total_count):
                self._spawn_service(execution, service, counter)

    def _spawn_service(self, execution: execution_module.Execution, service_description: application_module.ServiceDescription, counter) -> bool:
        copts = DockerContainerOptions()
        copts.gelf_log_address = get_conf().gelf_address
        copts.name = service_description.name + "-" + str(counter) + "-" + execution.name + "-" + execution.owner.name + "-" + get_conf().deployment_name + "-zoe"
        copts.set_memory_limit(service_description.required_resources['memory'])
        copts.network_name = get_conf().overlay_network_name
        service_id = self.state_manager.gen_id()
        copts.labels = {
            'zoe.execution.name': execution.name,
            'zoe.execution.id': str(execution.id),
            'zoe.service.name': service_description.name + "-" + str(counter),
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
            'deployment_name': get_conf().deployment_name,
            'index': counter
        }
        for env_name, env_value in service_description.environment:
            try:
                env_value = env_value.format(**subst_dict)
            except KeyError:
                raise ZoeException("cannot find variable to substitute in expression {}".format(env_value))
            copts.add_env_variable(env_name, env_value)

        for p in service_description.ports:
            if p.expose:
                copts.ports.append(p.port_number)  # FIXME UDP ports?

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

    def execution_terminate(self, execution: execution_module.Execution, reason, message=None):
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
            if message is not None:
                execution.error = message
            else:
                execution.error = 'error'
            return
        elif reason == 'finished':
            execution.set_finished()
        else:
            execution.set_terminated()
        self.scheduler.execution_terminate(execution)

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

        # ### Check executions and container consistency
        swarm_containers = self.swarm.list(only_label={'zoe.deployment_name': get_conf().deployment_name})
        conts_state_to_delete = []
        for c_id, c in self.state_manager.services.items():
            if c.docker_id not in [x['id'] for x in swarm_containers]:
                log.error('fixed: removing from state container {} that does not exist in Swarm'.format(c.name))
                conts_state_to_delete.append(c_id)
        for c_id in conts_state_to_delete:
            self.state_manager.delete('service', c_id)
            state_changed = True

        if state_changed:
            self.state_manager.state_updated()
