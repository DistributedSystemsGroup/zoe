from io import BytesIO
import logging
import zipfile

from zoe_scheduler.swarm_client import SwarmClient, ContainerOptions
from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.cluster import ClusterState
from zoe_scheduler.state.container import ContainerState
from zoe_scheduler.state.execution import ExecutionState
from zoe_scheduler.exceptions import CannotCreateCluster
from zoe_scheduler.application_description import ZoeApplicationProcess
from zoe_scheduler.object_storage import logs_archive_upload, generate_application_binary_url

log = logging.getLogger(__name__)


class PlatformManager:
    def __init__(self):
        self.swarm = SwarmClient()

    def start_execution(self, execution_id: int, resources: dict) -> bool:
        state = AlchemySession()
        execution = state.query(ExecutionState).filter_by(id=execution_id).one()
        execution.assigned_resources = resources
        try:
            self._application_to_containers(state, execution)
        except CannotCreateCluster:
            return False
        execution.set_started()
        state.commit()
        return True

    def _application_to_containers(self, state: AlchemySession, execution: ExecutionState):
        # TODO: use the resources assigned by the scheduler, not the ones required by the application
        cluster = ClusterState(execution_id=execution.id)
        execution.cluster = cluster
        for process in execution.application.description.processes:
            self._spawn_process(state, execution, process)

    def _spawn_process(self, state: AlchemySession, execution: ExecutionState, process_description: ZoeApplicationProcess) -> bool:
        opts = ContainerOptions()
        opts.set_memory_limit(process_description.required_resources['memory'])

        # Generate a dictionary containing the current cluster status (before the new container is spawned)
        # This information is used to substitute templates in the environment variables
        subst_dict = {
            "cluster": execution.gen_environment_substitution(),
            "application_binary_url": generate_application_binary_url(execution.application)
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

    def execution_terminate(self, state: AlchemySession, execution: ExecutionState):
        cluster = execution.cluster
        logs = []
        if cluster is not None:
            containers = cluster.containers
            for c in containers:
                logs.append((c.readable_name, c.ip_address, self.log_get(c)))
                self.swarm.terminate_container(c.docker_id)
                state.delete(c)
            state.delete(cluster)
        execution.set_terminated()
        self._archive_execution_logs(execution, logs)

    def log_get(self, container: ContainerState) -> str:
        return self.swarm.log_get(container.docker_id)

    def _archive_execution_logs(self, execution: ExecutionState, logs: list):
        zipdata = BytesIO()
        with zipfile.ZipFile(zipdata, "w", compression=zipfile.ZIP_DEFLATED) as logzip:
            for c in logs:
                fname = c[0] + "-" + c[1] + ".txt"
                logzip.writestr(fname, c[2])
        logs_archive_upload(execution, zipdata.getvalue())

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
                self._container_died(state, c)

        state.commit()
        state.close()

    def _container_died(self, state: AlchemySession, container: ContainerState):
        if container.monitor:
            log.debug("found a dead monitor container, cleaning up execution")
            self.execution_terminate(state, container.cluster.execution)
            container.cluster.execution.set_finished()
#            notify_execution_finished(container.cluster.execution)
        else:
            log.warning("Container {} (ID: {}) died unexpectedly".format(container.readable_name, container.id))

    def container_stats(self, container_id):
        state = AlchemySession()
        container = state.query(ContainerState).filter_by(id=container_id).one()
        return self.swarm.stats(container.docker_id)
