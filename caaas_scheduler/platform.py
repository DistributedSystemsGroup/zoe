from caaas_scheduler.swarm_client import SwarmClient, ContainerOptions

from common.state import AlchemySession, Cluster, Container, Application, SparkApplication, Proxy, Execution
from common.application_resources import ApplicationResources, SparkApplicationResources
from common.exceptions import CannotCreateCluster


class PlatformManager:
    def __init__(self):
        self.swarm = SwarmClient()

    def start_execution(self, execution_id: int, resources: ApplicationResources) -> bool:
        state = AlchemySession()
        execution = state.query(Execution).filter_by(id=execution_id).one()
        execution.assigned_resources = resources
        self._application_to_containers(state, execution)
        execution.set_started()
        state.commit()
        return True

    # noinspection PyTypeChecker
    def _application_to_containers(self, state, execution: Execution):
        if type(execution.application) is SparkApplication:
            self._spark_app_to_containers(state, execution)
        else:
            raise NotImplementedError('%s application are not implemented' % type(execution.application))

    def _spark_app_to_containers(self, state: AlchemySession, execution: Execution):
        application = execution.application
        resources = execution.assigned_resources
        cluster = Cluster(execution_id=execution.id)
        state.add(cluster)
        # Master
        master_requirements = resources.master_resources
        master_opts = ContainerOptions()
        if "memory_limit" in master_requirements:
            master_opts.set_memory_limit(master_requirements["memory_limit"])
        image = application.master_image
        master_info = self.swarm.spawn_container(image, master_opts)
        if master_info is None:
            raise CannotCreateCluster(application)
        container = Container(docker_id=master_info["docker_id"], ip_address=master_info["ip_address"], readable_name="spark-master", cluster=cluster)
        state.add(container)
        master_web_url = "http://" + master_info["ip_address"] + ":8080"
        master_proxy = Proxy(service_name="Spark master web interface", container=container, cluster=cluster, internal_url=master_web_url)
        state.add(master_proxy)

        # Workers
        worker_requirements = resources.worker_resources
        worker_opts = ContainerOptions()
        worker_opts.add_env_variable("SPARK_MASTER_IP", master_info["ip_address"])
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
                self.swarm.terminate_container(master_info["docker_id"])
                for j in range(i):
                    self.swarm.terminate_container(workers_docker_id[j])
                raise CannotCreateCluster(application)
            workers_docker_id.append(worker_info["docker_id"])
            container = Container(docker_id=worker_info["docker_id"], ip_address=worker_info["ip_address"], readable_name="spark-worker-%d" % i)
            container.cluster = cluster
            state.add(container)
            worker_web_url = "http://" + worker_info["ip_address"] + ":8081"
            worker_proxy = Proxy(service_name="Spark worker web interface", container=container, cluster=cluster, internal_url=worker_web_url)
            state.add(worker_proxy)

    def terminate_execution(self, execution: Execution):
        state = AlchemySession()
        cluster = state.query(Cluster).filter_by(execution_id=execution.id).one()
        containers = cluster.containers
        for c in containers:
            self.swarm.terminate_container(c.docker_id)
            state.delete(c)
        for p in cluster.proxies:
            state.delete(p)
        state.delete(cluster)
        execution.set_terminated()
        state.commit()
