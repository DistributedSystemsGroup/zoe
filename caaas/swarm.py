from docker import Client
from docker import errors as docker_errors
from docker.utils import create_host_config
from threading import Thread
import time
from uuid import uuid4 as uuid

from caaas import get_db


REGISTRY = "10.0.0.2:5000"
MASTER_IMAGE = REGISTRY + "/venza/spark-master:1.4.1"
WORKER_IMAGE = REGISTRY + "/venza/spark-worker:1.4.1"
SHELL_IMAGE = REGISTRY + "/venza/spark-shell:1.4.1"
SUBMIT_IMAGE = REGISTRY + "/venza/spark-submit:1.4.1"
CONTAINER_IMAGE = REGISTRY + "/venza/spark-notebook:1.4.1"


def get_uuid():
    return str(uuid())


class SwarmStatus:
    def __init__(self):
        self.num_nodes = 0
        self.num_containers = 0


class Swarm:
    def __init__(self):
        self.status = SwarmStatus()
        self.cli = None
        self.manager = None

    def connect(self, swarm_manager):
        self.manager = swarm_manager
        self.cli = Client(base_url="tcp://" + self.manager)

    def start_update_thread(self):
        assert self.manager is not None
        th = Thread(target=self._thread_cb)
        th.start()

    def _thread_cb(self):
        print("Stats update thread started")
        while True:
            self.update_status()
            time.sleep(1)

    def update_status(self):
        assert self.cli is not None
        info = self.cli.info()
        self.status.num_containers = info["Containers"]
        self.status.num_nodes = info["DriverStatus"][3][1]

    def get_notebook(self, user_id):
        db = get_db()
        nb = db.get_notebook(user_id)
        if nb is None:
            self.start_cluster_with_notebook(user_id)
            nb = db.get_notebook(user_id)
        return nb["address"]

    def start_cluster_with_notebook(self, user_id):
        num_workers = 2
        self._create_new_spark_cluster(user_id, "notebook", num_workers, with_notebook=True)

    def _create_new_spark_cluster(self, user_id, name, num_workers, with_notebook):
        db = get_db()
        try:
            cluster_id = db.new_cluster(user_id, name)
            master_info = self._spawn_spark_master(cluster_id, user_id)
            db.set_master_address(cluster_id, master_info["spark_master_address"])
            for i in range(num_workers):
                self._spawn_spark_worker(cluster_id, user_id, master_info)
            if with_notebook:
                self._spawn_spark_notebook(cluster_id, user_id, master_info)
        except docker_errors.APIError as e:
            print("Error starting container: " + str(e.explanation))
            # FIXME: should rollback all changes to DB

    def _spawn_spark_master(self, cluster_id, user_id):
        db = get_db()
        options = {
            "environment": {},
        }
        info = self._spawn_container(MASTER_IMAGE, options)
        info["spark_master_address"] = "http://" + info["docker_ip"] + ":8080"
        cont_id = db.new_container(cluster_id, user_id, info["docker_id"], info["docker_ip"], "spark-master")
        db.new_proxy_entry(get_uuid(), cluster_id, info["spark_master_address"], "spark-master", cont_id)
        return info

    def _spawn_spark_worker(self, cluster_id, user_id, master_info):
        db = get_db()
        options = {
            "environment": {
                "SPARK_MASTER_IP": master_info["docker_ip"],
                "SPARK_WORKER_RAM": "4g",
                "SPARK_WORKER_CORES": "2"
            },
        }
        info = self._spawn_container(WORKER_IMAGE, options)
        cont_id = db.new_container(cluster_id, user_id, info["docker_id"], info["docker_ip"], "spark-worker")
        db.new_proxy_entry(get_uuid(), cluster_id, "http://" + info["docker_ip"] + ":8081", "spark-worker", cont_id)
        return info

    def _spawn_spark_notebook(self, cluster_id, user_id, master_info):
        db = get_db()
        proxy_id = get_uuid()
        options = {
            "environment": {
                "SPARK_MASTER_IP": master_info["docker_ip"],
                "PROXY_ID": proxy_id
            },
        }
        info = self._spawn_container(CONTAINER_IMAGE, options)
        cont_id = db.new_container(cluster_id, user_id, info["docker_id"], info["docker_ip"], "spark-notebook")
        db.new_proxy_entry(proxy_id, cluster_id, "http://" + info["docker_ip"] + ":9000/proxy/" + proxy_id, "spark-notebook", cont_id)
        db.new_notebook(cluster_id, "http://bigfoot-m2.eurecom.fr/proxy/" + proxy_id, user_id, cont_id)
        return info

    def _spawn_container(self, image, options):
        host_config = create_host_config(network_mode="bridge")
        cont = self.cli.create_container(image=image,
                                         environment=options["environment"],
                                         network_disabled=False,
                                         host_config=host_config,
                                         detach=True)
        self.cli.start(container=cont.get('Id'))
        docker_info = self.cli.inspect_container(container=cont.get('Id'))
        info = {
            "docker_id": cont.get("Id"),
            "docker_ip": docker_info["NetworkSettings"]["IPAddress"]
        }
        return info

swarm = Swarm()
