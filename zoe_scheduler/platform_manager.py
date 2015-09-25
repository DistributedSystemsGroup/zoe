import logging

from common.application_description import ZoeApplication, ZoeApplicationProcess
from common.exceptions import CannotCreateCluster
from common.zoe_storage_client import generate_application_binary_url, logs_archive_create
from zoe_scheduler.platform_status import PlatformStatus
from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.cluster import ClusterState
from zoe_scheduler.state.container import ContainerState
from zoe_scheduler.state.execution import ExecutionState
from zoe_scheduler.swarm_client import SwarmClient, ContainerOptions
from zoe_scheduler.stats import ContainerStats

log = logging.getLogger(__name__)


class PlatformManager:
    def __init__(self, scheduler):
        self.swarm = SwarmClient()
        self.status = PlatformStatus(scheduler)
        scheduler.platform = self

    def start_execution(self, execution_id: int, app_description: ZoeApplication) -> bool:
        state = AlchemySession()
        execution = state.query(ExecutionState).filter_by(id=execution_id).one()
        execution.app_description = app_description
        try:
            self._application_to_containers(state, execution)
        except CannotCreateCluster:
            return False
        execution.set_started()
        state.commit()
        return True

    def _application_to_containers(self, state: AlchemySession, execution: ExecutionState):
        cluster = ClusterState(execution_id=execution.id)
        execution.cluster = cluster
        for process in execution.app_description.processes:
            self._spawn_process(state, execution, process)

    def _spawn_process(self, state: AlchemySession, execution: ExecutionState, process_description: ZoeApplicationProcess) -> bool:
        opts = ContainerOptions()
        opts.set_memory_limit(process_description.required_resources['memory'])

        # Generate a dictionary containing the current cluster status (before the new container is spawned)
        # This information is used to substitute templates in the environment variables
        subst_dict = {
            "cluster": execution.gen_environment_substitution(),
            "application_binary_url": generate_application_binary_url(execution.application_id)
        }
        for env_name, env_value in process_description.environment:
            try:
                env_value = env_value.format(**subst_dict)
            except KeyError:
                log.error("cannot find variable to substitute in expression {}".format(env_value))
                raise CannotCreateCluster(execution)
            opts.add_env_variable(env_name, env_value)

        # The same dictionary is used for templates in the command
        if process_description.command is not None:
            opts.set_command(process_description.command.format(**subst_dict))

        cont_info = self.swarm.spawn_container(process_description.docker_image, opts)
        if cont_info is None:
            raise CannotCreateCluster(execution)
        container = ContainerState(docker_id=cont_info["docker_id"],
                                   ip_address=cont_info["ip_address"],
                                   readable_name=process_description.name,
                                   cluster=execution.cluster,
                                   monitor=process_description.monitor)
        state.add(container)
        state.commit()
        return True

    def execution_terminate(self, execution: ExecutionState):
        cluster = execution.cluster
        for c in cluster.containers:
            if c.monitor:
                self.swarm.terminate_container(c.docker_id, delete=False)
                return

    def log_get(self, container: ContainerState) -> str:
        return self.swarm.log_get(container.docker_id)

    def container_stats(self, container_id: int) -> ContainerStats:
        state = AlchemySession()
        container = state.query(ContainerState).filter_by(id=container_id).one()
        return self.swarm.stats(container.docker_id)

    def is_container_alive(self, container: ContainerState) -> bool:
        ret = self.swarm.inspect_container(container.docker_id)
        if ret is None:
            return False
        return ret["running"]

    def check_executions_health(self):
        state = AlchemySession()
        all_containers = state.query(ContainerState).all()
        for c in all_containers:
            if not self.is_container_alive(c):
                if c.cluster.execution.status == "running":
                    self._container_died(state, c)

        state.commit()
        state.close()

    def _container_died(self, state: AlchemySession, container: ContainerState):
        if container.monitor:
            log.debug("found a dead monitor container, cleaning up execution")
            container.cluster.execution.set_cleaning_up()
            state.commit()
            self._cleanup_execution(state, container.cluster.execution)
            container.cluster.execution.set_finished()
#            notify_execution_finished(container.cluster.execution)
        else:
            log.warning("Container {} (ID: {}) died unexpectedly".format(container.readable_name, container.id))

    def _cleanup_execution(self, state: AlchemySession, execution: ExecutionState):
        cluster = execution.cluster
        logs = []
        if cluster is not None:
            containers = cluster.containers
            for c in containers:
                l = self.log_get(c)
                if l is not None:
                    logs.append((c.readable_name, c.ip_address, l))
                self.swarm.terminate_container(c.docker_id, delete=True)
                state.delete(c)
            state.delete(cluster)
        execution.set_terminated()
        logs_archive_create(execution.id, logs)
