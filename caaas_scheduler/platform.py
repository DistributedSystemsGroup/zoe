from caaas_scheduler.swarm_client import SwarmClient, ContainerOptions

from common.state import AlchemySession, Cluster, Container, Application, SparkApplication
from common.application_resources import ApplicationResources, SparkApplicationResources


class PlatformManager:
    def __init__(self):
        self.swarm = SwarmClient()

    def start_application(self, application: Application, resources: ApplicationResources):
        state = AlchemySession()
        self._application_to_containers(state, application, resources)
        state.commit()

    # noinspection PyTypeChecker
    def _application_to_containers(self, state, application: Application, resources: ApplicationResources):
        if type(application) is SparkApplication:
            self._spark_app_to_containers(state, application, resources)
        else:
            raise NotImplementedError('%s application are not implemented' % type(application))

    def _spark_app_to_containers(self, state: AlchemySession, application: SparkApplication, resources: SparkApplicationResources):
        cluster = Cluster(app_id=application.id)
        state.add(cluster)
        # Master
        master_requirements = resources.master_resources
        master_opts = ContainerOptions()
        if "memory_limit" in master_requirements:
            master_opts.set_memory_limit(master_requirements["memory_limit"])
        image = application.master_image
        master_info = self.swarm.spawn_container(image, master_opts)
        container = Container(docker_id=master_info["docker_id"], ip_address=master_info["ip_address"], readable_name="spark-master")
        container.cluster = cluster
        state.add(container)

        # Workers
        worker_requirements = resources.worker_resources
        worker_opts = ContainerOptions()
        worker_opts.add_env_variable("SPARK_MASTER_IP", master_info["docker_ip"])
        if "memory_limit" in worker_requirements:
            worker_opts.add_env_variable("SPARK_WORKER_RAM", worker_requirements["memory_limit"])
            worker_opts.set_memory_limit(worker_requirements["memory_limit"])
        if "worker_cores" in worker_requirements:
            worker_opts.add_env_variable("SPARK_WORKER_CORES", worker_requirements["worker_cores"])
        image = application.worker_image
        for i in range(resources.worker_count):
            worker_info = self.swarm.spawn_container(image, worker_opts)
            container = Container(docker_id=worker_info["docker_id"], ip_address=worker_info["ip_address"], readable_name="spark-worker-%d" % i)
            container.cluster = cluster
            state.add(container)

    def terminate_application(self, application: Application):
        state = AlchemySession()
        cluster = state.query(Cluster).filter_by(app_id=application.id)
        containers = cluster.containers
        for c in containers:
            self.swarm.terminate_container(c.docker_id)
            state.delete(c)
        state.delete(cluster)
        state.commit()
