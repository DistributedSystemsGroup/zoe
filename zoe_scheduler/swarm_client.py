import time
import logging

import docker
import docker.utils
import docker.errors

from common.configuration import zoeconf
from zoe_scheduler.stats import SwarmStats, SwarmNodeStats, ContainerStats

log = logging.getLogger(__name__)


class SwarmClient:
    def __init__(self):
        manager = zoeconf().docker_swarm_manager
        self.cli = docker.Client(base_url=manager)

    def info(self) -> SwarmStats:
        info = self.cli.info()
        pl_status = SwarmStats()
        pl_status.container_count = info["Containers"]
        pl_status.image_count = info["Images"]
        pl_status.memory_total = info["MemTotal"]
        pl_status.cores_total = info["NCPU"]

        # DriverStatus is a list...
        idx = 1
        assert 'Strategy' in info["DriverStatus"][idx][0]
        pl_status.placement_strategy = info["DriverStatus"][idx][1]
        idx = 2
        assert 'Filters' in info["DriverStatus"][idx][0]
        pl_status.active_filters = [x.strip() for x in info["DriverStatus"][idx][1].split(", ")]
        idx = 3
        assert 'Nodes' in info["DriverStatus"][idx][0]
        node_count = int(info["DriverStatus"][idx][1])
        idx = 4
        for node in range(node_count):
            ns = SwarmNodeStats(info["DriverStatus"][idx + node][0])
            ns.docker_endpoint = info["DriverStatus"][idx + node][1]
            ns.container_count = int(info["DriverStatus"][idx + node + 1][1])
            ns.cores_reserved = int(info["DriverStatus"][idx + node + 2][1].split(' / ')[0])
            ns.cores_total = int(info["DriverStatus"][idx + node + 2][1].split(' / ')[1])
            ns.memory_reserved = info["DriverStatus"][idx + node + 3][1].split(' / ')[0]
            ns.memory_total = info["DriverStatus"][idx + node + 3][1].split(' / ')[1]
            ns.labels = info["DriverStatus"][idx + node + 4][1:]

            pl_status.nodes.append(ns)
            idx += 4
        pl_status.timestamp = time.time()
        return pl_status

    def spawn_container(self, image, options) -> dict:
        cont = None
        try:
            host_config = docker.utils.create_host_config(network_mode="bridge",
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
        except docker.errors.APIError as e:
            if cont is not None:
                self.cli.remove_container(container=cont.get('Id'), force=True)
            log.error(str(e))
            return None
        info = self.inspect_container(cont.get('Id'))
        return info

    def inspect_container(self, docker_id) -> dict:
        try:
            docker_info = self.cli.inspect_container(container=docker_id)
        except docker.errors.APIError:
            return None
        info = {
            "ip_address": docker_info["NetworkSettings"]["IPAddress"],
            "docker_id": docker_id
        }
        if docker_info["State"]["Running"]:
            info["state"] = "running"
            info["running"] = True
        elif docker_info["State"]["Paused"]:
            info["state"] = "paused"
            info["running"] = True
        elif docker_info["State"]["Restarting"]:
            info["state"] = "restarting"
            info["running"] = True
        elif docker_info["State"]["OOMKilled"]:
            info["state"] = "killed"
            info["running"] = False
        elif docker_info["State"]["Dead"]:
            info["state"] = "killed"
            info["running"] = False
        else:
            info["state"] = "unknown"
            info["running"] = False
        return info

    def terminate_container(self, docker_id):
        self.cli.remove_container(docker_id, force=True)

    def log_get(self, docker_id) -> str:
        logdata = self.cli.logs(container=docker_id, stdout=True, stderr=True, stream=False, timestamps=False, tail="all")
        return logdata.decode("utf-8")

    def stats(self, docker_id) -> ContainerStats:
        stats_stream = self.cli.stats(docker_id, decode=True)
        for s in stats_stream:
            return ContainerStats(s)


class ContainerOptions:
    def __init__(self):
        self.env = {}
        self.volume_binds = []
        self.volumes = []
        self.command = ""
        self.memory_limit = '2g'

    def add_env_variable(self, name, value):
        if value is not None:
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
