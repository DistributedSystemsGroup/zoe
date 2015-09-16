from datetime import datetime, timedelta
import logging
from io import BytesIO
import zipfile

from zoe_scheduler.swarm_client import SwarmClient, ContainerOptions
from zoe_scheduler.proxy_manager import proxy_manager
from zoe_scheduler.emails import notify_execution_finished, notify_notebook_notice, notify_notebook_termination
from zoe_scheduler.state import AlchemySession
from zoe_scheduler.state.application import SparkApplicationState, SparkNotebookApplicationState, SparkSubmitApplicationState
from zoe_scheduler.state.cluster import ClusterState
from zoe_scheduler.state.container import ContainerState
from zoe_scheduler.state.execution import ExecutionState, SparkSubmitExecutionState
from zoe_scheduler.state.proxy import ProxyState
from common.application_resources import ApplicationResources
from zoe_scheduler.exceptions import CannotCreateCluster
from common.configuration import zoeconf
from zoe_scheduler.object_storage import logs_archive_upload
from zoe_scheduler.urls import generate_application_binary_url

log = logging.getLogger(__name__)


class PlatformManager:
    def __init__(self):
        self.swarm = SwarmClient()

    def start_execution(self, execution_id: int, resources: ApplicationResources) -> bool:
        state = AlchemySession()
        execution = state.query(ExecutionState).filter_by(id=execution_id).one()
        execution.assigned_resources = resources
        try:
            self._application_to_containers(state, execution)
        except CannotCreateCluster:
            return False
        execution.set_started()
        state.commit()
        proxy_manager().update_proxy()
        return True

    def _application_to_containers(self, state: AlchemySession, execution: ExecutionState):
        cluster = ClusterState(execution_id=execution.id)
        state.add(cluster)
        if isinstance(execution.application, SparkApplicationState):
            master_container = self._spawn_master(state, execution, cluster)
            self._spawn_workers(state, execution, cluster, master_container)
            if isinstance(execution.application, SparkNotebookApplicationState):
                self._spawn_notebook(state, execution, cluster, master_container)
            elif isinstance(execution.application, SparkSubmitApplicationState):
                self._spawn_submit_client(state, execution, cluster, master_container)
        else:
            raise NotImplementedError('%s applications are not implemented' % type(execution.application))

    def _spawn_master(self, state: AlchemySession, execution: ExecutionState, cluster: ClusterState) -> ContainerState:
        application = execution.application
        resources = execution.assigned_resources
        master_requirements = resources.master_resources
        master_opts = ContainerOptions()
        if "memory_limit" in master_requirements:
            master_opts.set_memory_limit(master_requirements["memory_limit"])
        image = application.master_image
        master_info = self.swarm.spawn_container(image, master_opts)
        if master_info is None:
            raise CannotCreateCluster(application)
        container = ContainerState(docker_id=master_info["docker_id"], ip_address=master_info["ip_address"], readable_name="spark-master", cluster=cluster)
        state.add(container)
        master_web_url = "http://" + master_info["ip_address"] + ":8080"
        master_proxy = ProxyState(service_name="Spark master web interface", container=container, cluster=cluster, internal_url=master_web_url)
        state.add(master_proxy)
        return container

    def _spawn_workers(self, state: AlchemySession, execution: ExecutionState, cluster: ClusterState, master: ContainerState):
        application = execution.application
        resources = execution.assigned_resources
        worker_requirements = resources.worker_resources
        worker_opts = ContainerOptions()
        worker_opts.add_env_variable("SPARK_MASTER_IP", master.ip_address)
        if "memory_limit" in worker_requirements:
            worker_opts.add_env_variable("SPARK_WORKER_RAM", worker_requirements["memory_limit"])
            worker_opts.set_memory_limit(worker_requirements["memory_limit"])
        if "cores" in worker_requirements:
            worker_opts.add_env_variable("SPARK_WORKER_CORES", worker_requirements["cores"])
        image = application.worker_image
        workers_docker_id = []
        for i in range(resources.worker_count):
            worker_info = self.swarm.spawn_container(image, worker_opts)
            if worker_info is None:
                self.swarm.terminate_container(master.docker_id)
                for j in range(i):
                    self.swarm.terminate_container(workers_docker_id[j])
                raise CannotCreateCluster(application)
            workers_docker_id.append(worker_info["docker_id"])
            container = ContainerState(docker_id=worker_info["docker_id"], ip_address=worker_info["ip_address"], readable_name="spark-worker-%d" % i)
            container.cluster = cluster
            state.add(container)
            worker_web_url = "http://" + worker_info["ip_address"] + ":8081"
            worker_proxy = ProxyState(service_name="Spark worker web interface", container=container, cluster=cluster, internal_url=worker_web_url)
            state.add(worker_proxy)

    def _spawn_notebook(self, state: AlchemySession, execution: ExecutionState, cluster: ClusterState, master: ContainerState):
        application = execution.application
        resources = execution.assigned_resources
        nb_requirements = resources.notebook_resources

        # Create this proxy entry here as we need to pass the ID in the container environment
        container = ContainerState(readable_name="spark-notebook", cluster=cluster)
        state.add(container)
        nb_url_proxy = ProxyState(service_name="Spark Notebook interface", container=container, cluster=cluster)
        state.add(nb_url_proxy)
        state.flush()

        nb_opts = ContainerOptions()
        nb_opts.add_env_variable("SPARK_MASTER_IP", master.ip_address)
        nb_opts.add_env_variable("PROXY_ID", nb_url_proxy.id)
        if "memory_limit" in execution.assigned_resources.worker_resources:
            nb_opts.add_env_variable("SPARK_EXECUTOR_RAM", execution.assigned_resources.worker_resources["memory_limit"])
        if "memory_limit" in nb_requirements:
            nb_opts.set_memory_limit(nb_requirements["memory_limit"])
        image = application.notebook_image
        nb_info = self.swarm.spawn_container(image, nb_opts)
        if nb_info is None:
            self.swarm.terminate_container(master.docker_id)
            # FIXME terminate all containers in case of error

        container.docker_id = nb_info["docker_id"]
        container.ip_address = nb_info["ip_address"]

        nb_app_url = "http://" + nb_info["ip_address"] + ":4040"
        nb_app_proxy = ProxyState(service_name="Spark application web interface", container=container, cluster=cluster, internal_url=nb_app_url)
        state.add(nb_app_proxy)
        nb_url_proxy.internal_url = "http://" + nb_info["ip_address"] + ":9000/proxy/%d" % nb_url_proxy.id

    def _spawn_submit_client(self, state: AlchemySession, execution: SparkSubmitExecutionState, cluster: ClusterState, master: ContainerState):
        application = execution.application
        resources = execution.assigned_resources
        requirements = resources.client_resources

        # Do this here so we can use the ID later for building proxy URLs
        container = ContainerState(readable_name="spark-submit", cluster=cluster)
        state.add(container)
        state.flush()

        cli_opts = ContainerOptions()
        cli_opts.add_env_variable("SPARK_MASTER_IP", master.ip_address)
        cli_opts.add_env_variable("PROXY_ID", container.id)
        cli_opts.add_env_variable("APPLICATION_ID", application.id)
        cli_opts.add_env_variable("SPARK_OPTIONS", execution.spark_opts)
        cli_opts.add_env_variable("APPLICATION_URL", generate_application_binary_url(application))
        cli_opts.add_env_variable("SPARK_OPTIONS", execution.spark_opts)
        if "memory_limit" in execution.assigned_resources.worker_resources:
            cli_opts.add_env_variable("SPARK_EXECUTOR_RAM", execution.assigned_resources.worker_resources["memory_limit"])
        if "memory_limit" in requirements:
            cli_opts.set_memory_limit(requirements["memory_limit"])
        image = application.submit_image
        cli_opts.set_command("/opt/submit.sh " + execution.commandline)
        cli_info = self.swarm.spawn_container(image, cli_opts)
        if cli_info is None:
            self.swarm.terminate_container(master.docker_id)
            # FIXME terminate all containers in case of error

        container.docker_id = cli_info["docker_id"]
        container.ip_address = cli_info["ip_address"]

        nb_app_url = "http://" + cli_info["ip_address"] + ":4040"
        nb_app_proxy = ProxyState(service_name="Spark application web interface", container=container, cluster=cluster, internal_url=nb_app_url)
        state.add(nb_app_proxy)

    def execution_terminate(self, state: AlchemySession, execution: ExecutionState):
        cluster = execution.cluster
        logs = []
        if cluster is not None:
            containers = cluster.containers
            for c in containers:
                logs.append((c.readable_name, c.ip_address, self.log_get(c)))
                self.swarm.terminate_container(c.docker_id)
                state.delete(c)
            for p in cluster.proxies:
                state.delete(p)
            state.delete(cluster)
        execution.set_terminated()
        self._archive_execution_logs(execution, logs)
        proxy_manager().update_proxy()

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
        return ret["running"]

    def check_executions_health(self):
        state = AlchemySession()
        all_containers = state.query(ContainerState).all()
        for c in all_containers:
            if not self.is_container_alive(c):
                self._container_died(state, c)

        notebooks = state.query(SparkNotebookApplicationState).all()
        for nb in notebooks:
            execs = nb.executions_running()
            for e in execs:
                c = e.find_container("spark-notebook")
                if c is not None:
                    pr = state.query(ProxyState).filter_by(container_id=c.id, service_name="Spark Notebook interface").one()
                    if datetime.now() - pr.last_access > timedelta(hours=zoeconf().notebook_max_age_no_activity):
                        log.info("Killing spark notebook {} for inactivity".format(e.id))
                        self.execution_terminate(state, e)
                        notify_notebook_termination(e)
                    if datetime.now() - pr.last_access > timedelta(hours=zoeconf().notebook_max_age_no_activity) - timedelta(hours=zoeconf().notebook_warning_age_no_activity):
                        if not e.termination_notice:
                            log.info("Spark notebook {} is on notice for inactivity".format(e.id))
                            e.termination_notice = True
                            notify_notebook_notice(e)

        state.commit()
        state.close()

    def _container_died(self, state: AlchemySession, container: ContainerState):
        if container.readable_name == "spark-submit" or container.readable_name == "spark-master":
            log.debug("found a dead spark-submit container, cleaning up")
            self.execution_terminate(state, container.cluster.execution)
            container.cluster.execution.set_finished()
            notify_execution_finished(container.cluster.execution)
        else:
            log.warning("Container {} (ID: {}) died unexpectedly")

    def container_stats(self, container_id):
        state = AlchemySession()
        container = state.query(ContainerState).filter_by(id=container_id).one()
        return self.swarm.stats(container.docker_id)
