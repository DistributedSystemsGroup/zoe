# Copyright (c) 2016, Daniele Venzano
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

"""Interface to the low-level Docker API."""

from argparse import Namespace
import time
import logging
from typing import Iterable, Callable, Dict, Any, Union

import humanfriendly

try:
    from kazoo.client import KazooClient
except ImportError:
    KazooClient = None

import docker
import docker.errors
import docker.utils

from zoe_master.stats import SwarmStats, SwarmNodeStats
from zoe_lib.exceptions import ZoeLibException

log = logging.getLogger(__name__)


class DockerContainerOptions:
    """Wrapper for the Docker container options."""
    def __init__(self):
        self.env = {}
        self.volume_binds = []
        self.volumes = []
        self.command = ""
        self.memory_limit = '2g'
        self.name = ''
        self.ports = []
        self.network_name = 'bridge'
        self.restart = True
        self.labels = []
        self.gelf_log_address = ''
        self.constraints = []

    def add_constraint(self, constraint):
        """Add a placement constraint (use docker syntax)."""
        self.constraints.append(constraint)

    def add_env_variable(self, name: str, value: Union[str, None]) -> None:
        """Add an environment variable to the container definition."""
        self.env[name] = value

    @property
    def environment(self) -> Dict[str, Union[str, None]]:
        """Access the environment variables."""
        return self.env

    def add_volume_bind(self, path: str, mountpoint: str, readonly=False) -> None:
        """Add a volume to the container."""
        self.volumes.append(mountpoint)
        self.volume_binds.append(path + ":" + mountpoint + ":" + ("ro" if readonly else "rw"))

    def get_volumes(self) -> Iterable[str]:
        """Get the volumes in Docker format."""
        return self.volumes

    def get_volume_binds(self) -> Iterable[str]:
        """Get the volumes in another Docker format."""
        return self.volume_binds

    def set_command(self, cmd) -> str:
        """Setter for the command to run in the container."""
        self.command = cmd

    def get_command(self) -> str:
        """Getter for the command to run in the container."""
        return self.command

    def set_memory_limit(self, limit: int):
        """Setter for the memory limit of the container."""
        self.memory_limit = limit

    def get_memory_limit(self) -> int:
        """Getter for the memory limit of the container."""
        return self.memory_limit

    @property
    def restart_policy(self) -> Dict[str, str]:
        """Getter for the restart policy of the container."""
        if self.restart:
            return {'Name': 'always'}
        else:
            return {}


def zookeeper_swarm(zk_server_list: str, path='/docker') -> str:
    """
    Given a Zookeeper server list, find the currently active Swarm master.
    :param zk_server_list: Zookeeper server list
    :param path: Swarm path in Zookeeper
    :return: Swarm master connection string
    """
    path += '/docker/swarm/leader'
    zk_client = KazooClient(hosts=zk_server_list)
    zk_client.start()
    master, stat_ = zk_client.get(path)
    zk_client.stop()
    return master.decode('utf-8')


class SwarmClient:
    """The Swarm client class that wraps the Docker API."""
    def __init__(self, opts: Namespace) -> None:
        self.opts = opts
        url = opts.swarm
        if 'zk://' in url:
            url = url[len('zk://'):]
            manager = zookeeper_swarm(url)
        elif 'http://' or 'https://' in url:
            manager = url
        else:
            raise ZoeLibException('Unsupported URL scheme for Swarm')
        log.debug('Connecting to Swarm at {}'.format(manager))
        self.cli = docker.Client(base_url=manager)

    def info(self) -> SwarmStats:
        """Retrieve Swarm statistics. The Docker API returns a mess difficult to parse."""
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
            idx2 = 0
            node_stats = SwarmNodeStats(info["DriverStatus"][idx + node][0])
            node_stats.docker_endpoint = info["DriverStatus"][idx + node][1]
            idx2 += 1
            if 'Status' in info["DriverStatus"][idx + node + idx2][0]:  # new docker version
                node_stats.status = info["DriverStatus"][idx + node + idx2][1]
                idx2 += 1
            node_stats.container_count = int(info["DriverStatus"][idx + node + idx2][1])
            idx2 += 1
            node_stats.cores_reserved = int(info["DriverStatus"][idx + node + idx2][1].split(' / ')[0])
            node_stats.cores_total = int(info["DriverStatus"][idx + node + idx2][1].split(' / ')[1])
            idx2 += 1
            node_stats.memory_reserved = info["DriverStatus"][idx + node + idx2][1].split(' / ')[0]
            node_stats.memory_total = info["DriverStatus"][idx + node + idx2][1].split(' / ')[1]
            idx2 += 1
            node_stats.labels = info["DriverStatus"][idx + node + idx2][1:]
            idx2 += 1
            node_stats.error = info["DriverStatus"][idx + node + idx2][1]
            idx2 += 1
            node_stats.last_update = info["DriverStatus"][idx + node + idx2][1]
            idx2 += 1
            node_stats.server_version = info["DriverStatus"][idx + node + idx2][1]

            node_stats.memory_reserved = humanfriendly.parse_size(node_stats.memory_reserved)
            node_stats.memory_total = humanfriendly.parse_size(node_stats.memory_total)

            pl_status.nodes.append(node_stats)
            idx += idx2
        pl_status.timestamp = time.time()
        return pl_status

    def spawn_container(self, image: str, options: DockerContainerOptions) -> Dict[str, Any]:
        """Create and start a new container."""
        cont = None
        port_bindings = {}  # type: Dict[str, Any]
        for port in options.ports:
            port_bindings[port] = None

        for constraint in options.constraints:
            options.add_env_variable(constraint, None)

        if options.gelf_log_address != '':
            log_config = docker.utils.LogConfig(type="gelf", config={'gelf-address': options.gelf_log_address, 'labels': ",".join(options.labels)})
        else:
            log_config = docker.utils.LogConfig(type="json-file")

        try:
            host_config = self.cli.create_host_config(network_mode=options.network_name,
                                                      binds=options.get_volume_binds(),
                                                      mem_limit=options.get_memory_limit(),
                                                      memswap_limit=options.get_memory_limit(),
                                                      restart_policy=options.restart_policy,
                                                      port_bindings=port_bindings,
                                                      log_config=log_config)
            cont = self.cli.create_container(image=image,
                                             environment=options.environment,
                                             network_disabled=False,
                                             host_config=host_config,
                                             detach=True,
                                             name=options.name,
                                             hostname=options.name,
                                             volumes=options.get_volumes(),
                                             command=options.get_command(),
                                             ports=options.ports,
                                             labels=options.labels)
            self.cli.start(container=cont.get('Id'))
        except Exception as e:
            if cont is not None:
                self.cli.remove_container(container=cont.get('Id'), force=True)
            raise ZoeLibException(str(e))

        info = self.inspect_container(cont.get('Id'))
        return info

    def inspect_container(self, docker_id: str) -> Dict[str, Any]:
        """Retrieve information about a running container."""
        try:
            docker_info = self.cli.inspect_container(container=docker_id)
        except Exception as e:
            raise ZoeLibException(str(e))

        info = {
            "docker_id": docker_id,
            "ip_address": {}
        }  # type: Dict[str, Any]
        for net in docker_info["NetworkSettings"]["Networks"]:
            if len(docker_info["NetworkSettings"]["Networks"][net]['IPAddress']) > 0:
                info["ip_address"][net] = docker_info["NetworkSettings"]["Networks"][net]['IPAddress']
            else:
                info["ip_address"][net] = None

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

        info['ports'] = {}
        if docker_info['NetworkSettings']['Ports'] is not None:
            for port in docker_info['NetworkSettings']['Ports']:
                if docker_info['NetworkSettings']['Ports'][port] is not None:
                    mapping = (
                        docker_info['NetworkSettings']['Ports'][port][0]['HostIp'],
                        docker_info['NetworkSettings']['Ports'][port][0]['HostPort']
                    )
                    info['ports'][port] = mapping
                else:
                    info['ports'][port] = None
        return info

    def terminate_container(self, docker_id: str, delete=False) -> None:
        """
        Terminate a container.

        :param docker_id: The container to terminate
        :type docker_id: str
        :param delete: If True, also delete the container files
        :type delete: bool
        :return: None
        """
        if delete:
            try:
                self.cli.remove_container(docker_id, force=True)
            except docker.errors.NotFound:
                log.warning("cannot remove a non-existent service")
        else:
            try:
                self.cli.kill(docker_id)
            except docker.errors.NotFound:
                log.warning("cannot remove a non-existent service")

    def event_listener(self, callback: Callable[[str], bool]) -> None:
        """An infinite loop that listens for events from Swarm."""
        for event in self.cli.events(decode=True):
            if not callback(event):
                break

    def connect_to_network(self, container_id: str, network_id: str) -> None:
        """Connect a container to a network."""
        try:
            self.cli.connect_container_to_network(container_id, network_id)
        except Exception as e:
            log.exception(str(e))

    def disconnect_from_network(self, container_id: str, network_id: str) -> None:
        """Disconnects a container from a network."""
        try:
            self.cli.disconnect_container_from_network(container_id, network_id)
        except Exception as e:
            log.exception(str(e))

    def list(self, only_label=None) -> Iterable[dict]:
        """
        List running or defined containers.

        :param only_label: filter containers with only a certain label
        :return: a list of containers
        """
        ret = self.cli.containers(all=True)
        conts = []
        for cont_info in ret:
            match = True
            for key, value in only_label.items():
                if key not in cont_info['Labels']:
                    match = False
                    break
                if cont_info['Labels'][key] != value:
                    match = False
                    break
            if match:
                aux = cont_info['Names'][0].split('/')  # Swarm returns container names in the form /host/name
                conts.append({
                    'id': cont_info['Id'],
                    'host': aux[1],
                    'name': aux[2],
                    'labels': cont_info['Labels'],
                    'status': cont_info['Status']
                })
        return conts
