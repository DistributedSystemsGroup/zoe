import logging

from common.application_description import ZoeApplication, ZoeApplicationProcess
from common.exceptions import CannotCreateCluster
from common.zoe_storage_client import logs_archive_create, generate_storage_url
from zoe_scheduler.dnsupdate import DDNSUpdater
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
        opts.name = process_description.name + "-{}".format(execution.id)
        opts.set_memory_limit(process_description.required_resources['memory'])

        # Generate a dictionary containing the current cluster status (before the new container is spawned)
        # This information is used to substitute templates in the environment variables
        subst_dict = {
            "cluster": execution.gen_environment_substitution(),
            "application_binary_url": generate_storage_url(execution.application_id, "apps")
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
                                   readable_name=opts.name,
                                   cluster=execution.cluster,
                                   description=process_description)
        state.add(container)
        state.commit()
        DDNSUpdater().add_a_record(container.readable_name, container.ip_address)
        return True

    def execution_terminate(self, execution: ExecutionState):
        """
        This method kills the "monitor" container, so that the cleanup thread will notice it and kill the other containers part of this cluster.
        The container is not deleted, so logs can be retrieved and saved.
        :param execution: The execution to be terminated
        :return:
        """
        cluster = execution.cluster
        for c in cluster.containers:
            assert isinstance(c, ContainerState)
            if c.description.monitor:
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
                if c.cluster.execution.status == "running" or c.cluster.execution.status == "cleaning up":
                    self._container_died(state, c)

        state.commit()
        state.close()

    def _container_died(self, state: AlchemySession, container: ContainerState):
        if container.description.monitor:
            self._cleanup_execution(state, container.cluster.execution)
            container.cluster.execution.set_finished()
#            notify_execution_finished(container.cluster.execution)
        else:
            log.warning("Container {} (ID: {}) died unexpectedly".format(container.description.name, container.id))

    def _cleanup_execution(self, state: AlchemySession, execution: ExecutionState):
        cluster = execution.cluster
        logs = []
        if cluster is not None:
            containers = cluster.containers
            for c in containers:
                assert isinstance(c, ContainerState)
                l = self.log_get(c)
                if l is not None:
                    logs.append((c.description.name, c.ip_address, l))
                self.swarm.terminate_container(c.docker_id, delete=True)
                state.delete(c)
                DDNSUpdater().delete_a_record(c.readable_name, c.ip_address)
            state.delete(cluster)
        execution.set_terminated()
        logs_archive_create(execution.id, logs)
