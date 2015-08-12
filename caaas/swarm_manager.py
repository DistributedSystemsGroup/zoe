from docker import Client
from docker import errors as docker_errors
from docker.utils import create_host_config
import time
import os

from caaas import CAaaState, SparkClusterDescription, AppHistory
from caaas.proxy_manager import get_notebook_address
from utils import config, get_uuid

REGISTRY = "10.0.0.2:5000"
MASTER_IMAGE = REGISTRY + "/venza/spark-master:1.4.1"
WORKER_IMAGE = REGISTRY + "/venza/spark-worker:1.4.1"
SHELL_IMAGE = REGISTRY + "/venza/spark-shell:1.4.1"
SUBMIT_IMAGE = REGISTRY + "/venza/spark-submit:1.4.1"
NOTEBOOK_IMAGE = REGISTRY + "/venza/spark-notebook:1.4.1"


class SwarmStatus:
    def __init__(self):
        self.num_nodes = 0
        self.num_containers = 0


class ContainerOptions:
    def __init__(self):
        self.env = {}
        self.volume_binds = []
        self.volumes = []
        self.command = ""
        self.memory_limit = '2g'

    def add_env_variable(self, name, value):
        self.env[name] = value

    def get_environment(self):
        return self.env

    def add_volume_bind(self, path, mountpoint, readonly=False):
        self.volumes.append(mountpoint)
        self.volume_binds.append(path + ":" + mountpoint + ":" + "ro" if readonly else "rw")

    def get_volumes(self):
        return self.volumes

    def get_volume_binds(self):
        return self.volume_binds

    def set_command(self, cmd):
        self.command = cmd

    def get_command(self):
        return self.command

    def set_memory_limit(self, limit):
        self.memory_limit = limit

    def get_memory_limit(self):
        return self.memory_limit


class SwarmManager:
    def __init__(self):
        self.status = SwarmStatus()
        self.cli = None
        self.last_update_timestamp = 0

    def connect(self):
        manager = config.get_swarm_manager_address()
        self.cli = Client(base_url=manager)

    def update_status(self):
        assert self.cli is not None
        info = self.cli.info()
        self.status.num_containers = info["Containers"]
        self.status.num_nodes = info["DriverStatus"][3][1]
        self.last_update_timestamp = time.time()

    def get_notebook(self, user_id):
        db = CAaaState()
        nb = db.get_notebook(user_id)
        if nb is None:
            self._start_cluster_with_notebook(user_id)
            nb = db.get_notebook(user_id)
        return get_notebook_address(nb)

    def spark_submit(self, user_id, app_id):
        cluster_id = self._start_cluster_for_app(user_id, app_id)
        return cluster_id

    def _start_cluster_with_notebook(self, user_id):
        cluster_descr = SparkClusterDescription()
        cluster_descr.for_spark_notebook()
        return self._create_new_spark_cluster(user_id, "notebook", cluster_descr, with_notebook=True)

    def _start_cluster_for_app(self, user_id: int, app_id: int):
        state = CAaaState()
        cluster_descr = SparkClusterDescription()
        cluster_descr.for_spark_app(app_id)
        cluster_id = self._create_new_spark_cluster(user_id, "spark-application", cluster_descr, app_id=app_id)
        state.application_started(app_id, cluster_id)
        return cluster_id

    def _create_new_spark_cluster(self, user_id, name, cluster_descr, with_notebook=False, app_id=None):
        db = CAaaState()
        try:
            cluster_id = db.new_cluster(user_id, name)
            master_info = self._spawn_spark_master(cluster_id, user_id, cluster_descr)
            db.set_master_address(cluster_id, master_info["spark_master_address"])
            for i in range(cluster_descr.num_workers):
                self._spawn_spark_worker(cluster_id, user_id, cluster_descr, master_info, i)
            if with_notebook:
                self._spawn_spark_notebook(cluster_id, user_id, cluster_descr, master_info)
            if app_id is not None:
                self._spawn_spark_submit(user_id, cluster_id, app_id, cluster_descr, master_info)
            return cluster_id
        except docker_errors.APIError as e:
            print("Error starting container: " + str(e.explanation))
            # FIXME: should rollback all changes to DB
            return None

    def _spawn_spark_master(self, cluster_id, user_id, cluster_descr):
        db = CAaaState()
        options = ContainerOptions()
        info = self._spawn_container(MASTER_IMAGE, options)
        info["spark_master_address"] = "http://" + info["docker_ip"] + ":8080"
        cont_id = db.new_container(cluster_id, user_id, info["docker_id"], info["docker_ip"], "spark-master")
        db.new_proxy_entry(get_uuid(), cluster_id, info["spark_master_address"], "web interface", cont_id)
        return info

    def _spawn_spark_worker(self, cluster_id, user_id, cluster_descr, master_info, count):
        db = CAaaState()
        options = ContainerOptions()
        options.add_env_variable("SPARK_MASTER_IP", master_info["docker_ip"])
        options.add_env_variable("SPARK_WORKER_RAM", cluster_descr.executor_ram_size)
        options.add_env_variable("SPARK_WORKER_CORES", cluster_descr.worker_cores)
        options.set_memory_limit(cluster_descr.executor_ram_size)
        info = self._spawn_container(WORKER_IMAGE, options)
        cont_id = db.new_container(cluster_id, user_id, info["docker_id"], info["docker_ip"], "spark-worker-" + str(count))
        db.new_proxy_entry(get_uuid(), cluster_id, "http://" + info["docker_ip"] + ":8081", "web interface", cont_id)
        return info

    def _spawn_spark_notebook(self, cluster_id, user_id, cluster_descr, master_info):
        db = CAaaState()
        proxy_id = get_uuid()
        options = ContainerOptions()
        options.add_env_variable("SPARK_MASTER_IP", master_info["docker_ip"])
        options.add_env_variable("SPARK_EXECUTOR_RAM", cluster_descr.executor_ram_size)
        options.add_env_variable("PROXY_ID", proxy_id)
        options.set_memory_limit(cluster_descr.executor_ram_size)
        info = self._spawn_container(NOTEBOOK_IMAGE, options)
        cont_id = db.new_container(cluster_id, user_id, info["docker_id"], info["docker_ip"], "spark-notebook")
        db.new_proxy_entry(proxy_id, cluster_id, "http://" + info["docker_ip"] + ":9000/proxy/" + proxy_id, "notebook", cont_id)
        db.new_proxy_entry(get_uuid(), cluster_id, "http://" + info["docker_ip"] + ":4040", "spark application", cont_id)
        return info

    def _spawn_spark_submit(self, user_id, cluster_id, app_id, cluster_descr, master_info):
        state = CAaaState()
        app = state.get_application(app_id)
        app["path"] = os.path.join(config.volume_path(), str(user_id), str(app_id))
        options = ContainerOptions()
        options.add_env_variable("SPARK_MASTER_IP", master_info["docker_ip"])
        options.add_env_variable("SPARK_EXECUTOR_RAM", cluster_descr.executor_ram_size)
        options.add_env_variable("SPARK_OPTIONS", app["spark_options"])
        options.add_volume_bind(app["path"], '/app', True)
        options.set_command("/opt/submit.sh /app " + app["cmd"])
        options.set_memory_limit(cluster_descr.executor_ram_size)
        info = self._spawn_container(SUBMIT_IMAGE, options)
        cont_id = state.new_container(cluster_id, user_id, info["docker_id"], info["docker_ip"], "spark-submit")
        state.new_proxy_entry(get_uuid(), cluster_id, "http://" + info["docker_ip"] + ":4040", "spark application", cont_id)
        return info

    def _spawn_container(self, image, options):
        host_config = create_host_config(network_mode="bridge",
                                         binds=options.get_volume_binds(),
                                         mem_limit=options.get_memory_limit())
        cont = self.cli.create_container(image=image,
                                         environment=options.get_environment(),
                                         network_disabled=False,
                                         host_config=host_config,
                                         detach=True,
                                         volumes=options.get_volumes(),
                                         command=options.get_command())
        self.cli.start(container=cont.get('Id'))
        docker_info = self.cli.inspect_container(container=cont.get('Id'))
        info = {
            "docker_id": cont.get("Id"),
            "docker_ip": docker_info["NetworkSettings"]["IPAddress"]
        }
        return info

    def _terminate_container(self, container_id, docker_id):
        db = CAaaState()
        db.remove_proxy(container_id)
        self.cli.remove_container(docker_id, force=True)
        db.remove_container(container_id)

    def terminate_cluster(self, cluster_id: int) -> bool:
        state = CAaaState()
        cont_list = state.get_containers(cluster_id=cluster_id)
        for cid, cinfo in cont_list.items():
            self._terminate_container(cid, cinfo["docker_id"])
        app_id = state.find_app_for_cluster(cluster_id)
        if app_id is not None:
            state.application_killed(cluster_id)
        state.remove_cluster(cluster_id)
        return True

    def get_log(self, container_id) -> bytes:
        db = CAaaState()
        cont = db.get_container(container_id)
        if len(cont) == 0:
            return None
        ret = self.cli.logs(container=cont["docker_id"], stdout=True, stderr=True, stream=False, timestamps=False, tail="all")
        return ret

    def save_logs(self, app_id, cluster_id):
        state = CAaaState()
        cluster = state.get_cluster(cluster_id)
        ah = AppHistory(cluster["user_id"])
        containers = state.get_containers(cluster_id=cluster_id)
        for cid, cinfo in containers.items():
            log = self.get_log(cid)
            ah.save_log(app_id, cinfo["contents"], log)

    def check_container_alive(self, container_id) -> bool:
        state = CAaaState()
        cont = state.get_container(container_id)
        if len(cont) == 0:
            return False
        ret = self.cli.inspect_container(container=cont["docker_id"])
        return ret["State"]["Running"]

    def swarm_status(self):
        return self.cli.info()
