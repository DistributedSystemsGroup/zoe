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

import time
import logging
from typing import Iterable, Callable, Dict, Any

import humanfriendly

try:
    from consul import Consul
except ImportError:
    Consul = None

try:
    from kazoo.client import KazooClient
except ImportError:
    KazooClient = None

import docker
import docker.tls
import docker.errors
import docker.utils
import docker.models.containers

import requests.packages

from zoe_lib.config import get_conf
from zoe_lib.state import Service
from zoe_master.stats import ClusterStats, NodeStats
from zoe_master.backends.service_instance import ServiceInstance
from zoe_master.exceptions import ZoeException, ZoeNotEnoughResourcesException

log = logging.getLogger(__name__)

try:
    docker.DockerClient()
except AttributeError:
    log.error('Docker package does not have the DockerClient attribute')
    raise ImportError('Wrong Docker library version')


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


def consul_swarm(consul_ip: str) -> str:
    """
    Using consul as discovery service, find the currently active Swarm master.
    :param consul_ip: consul ip address
    :return: Swarm master connection string
    """
    leader_key = 'docker/swarm/leader'
    consul_client = Consul(consul_ip)
    key_val = consul_client.kv.get(leader_key)
    master = key_val[1]['Value']
    return master.decode('utf-8')


class SwarmClient:
    """The Swarm client class that wraps the Docker API."""
    def __init__(self) -> None:
        url = get_conf().backend_swarm_url
        tls = False
        if 'zk://' in url:
            if KazooClient is None:
                raise ZoeException('ZooKeeper URL for Swarm, but the kazoo package is not installed')
            url = url[len('zk://'):]
            manager = zookeeper_swarm(url, get_conf().backend_swarm_zk_path)
        elif 'consul://' in url:
            if Consul is None:
                raise ZoeException('Consul URL for Swarm, but the consul package is not installed')
            url = url[len('consul://'):]
            manager = consul_swarm(url)
        elif 'http://' in url:
            manager = url
        elif 'https://' in url:
            tls = docker.tls.TLSConfig(client_cert=(get_conf().backend_swarm_tls_cert, get_conf().backend_swarm_tls_key), verify=get_conf().backend_swarm_tls_ca)
            manager = url
        else:
            raise ZoeException('Unsupported URL scheme for Swarm')
        self.cli = docker.DockerClient(base_url=manager, version="auto", tls=tls)

    def info(self) -> ClusterStats:
        """Retrieve Swarm statistics. The Docker API returns a mess difficult to parse."""
        info = self.cli.info()
        pl_status = ClusterStats()
        pl_status.container_count = info["Containers"]
        pl_status.memory_total = info["MemTotal"]
        pl_status.cores_total = info["NCPU"]

        # SystemStatus is a list...
        idx = 0  # Role, skip
        idx += 1
        assert 'Strategy' in info["SystemStatus"][idx][0]
        pl_status.placement_strategy = info["SystemStatus"][idx][1]
        idx += 1
        assert 'Filters' in info["SystemStatus"][idx][0]
        pl_status.active_filters = [x.strip() for x in info["SystemStatus"][idx][1].split(", ")]
        idx += 1
        assert 'Nodes' in info["SystemStatus"][idx][0]
        node_count = int(info["SystemStatus"][idx][1])
        idx += 1  # At index 4 the nodes begin
        for node in range(node_count):
            idx2 = 0
            node_stats = NodeStats(info["SystemStatus"][idx + node][0].strip())
            node_stats.docker_endpoint = info["SystemStatus"][idx + node][1]
            idx2 += 1  # ID, skip
            idx2 += 1  # Status
            node_stats.status = info["SystemStatus"][idx + node + idx2][1]
            idx2 += 1  # Containers
            node_stats.container_count = int(info["SystemStatus"][idx + node + idx2][1].split(' ')[0])
            idx2 += 1  # CPUs
            node_stats.cores_reserved = int(info["SystemStatus"][idx + node + idx2][1].split(' / ')[0])
            node_stats.cores_total = int(info["SystemStatus"][idx + node + idx2][1].split(' / ')[1])
            idx2 += 1  # Memory
            node_stats.memory_reserved = info["SystemStatus"][idx + node + idx2][1].split(' / ')[0]
            node_stats.memory_total = info["SystemStatus"][idx + node + idx2][1].split(' / ')[1]
            idx2 += 1  # Labels
            node_stats.labels = info["SystemStatus"][idx + node + idx2][1].split(', ')
            idx2 += 1  # Last update
            node_stats.last_update = info["SystemStatus"][idx + node + idx2][1]
            idx2 += 1  # Docker version
            node_stats.server_version = info["SystemStatus"][idx + node + idx2][1]

            node_stats.memory_reserved = humanfriendly.parse_size(node_stats.memory_reserved)
            node_stats.memory_total = humanfriendly.parse_size(node_stats.memory_total)

            pl_status.nodes.append(node_stats)
            idx += idx2
        pl_status.timestamp = time.time()
        return pl_status

    def spawn_container(self, service_instance: ServiceInstance) -> Dict[str, Any]:
        """Create and start a new container."""
        cont = None
        port_bindings = {}  # type: Dict[str, Any]
        for port in service_instance.ports:
            if port.expose:
                port_bindings[str(port.number) + '/tcp'] = None

        if get_conf().gelf_address != '':
            log_config = {
                "type": "gelf",
                "config": {
                    'gelf-address': get_conf().gelf_address,
                    'labels': ",".join(service_instance.labels)
                }
            }
        else:
            log_config = {
                "type": "json-file",
                "config": {}
            }

        environment = {}
        for name, value in service_instance.environment:
            environment[name] = value

        volumes = {}
        for volume in service_instance.volumes:
            if volume.type != "host_directory":
                log.error('Swarm backend does not support volume type {}'.format(volume.type))
            volumes[volume.path] = {'bind': volume.mount_point, 'mode': ("ro" if volume.readonly else "rw")}

        try:
            cont = self.cli.containers.run(image=service_instance.image_name,
                                           command=service_instance.command,
                                           detach=True,
                                           environment=environment,
                                           hostname=service_instance.hostname,
                                           labels=service_instance.labels,
                                           log_config=log_config,
                                           mem_limit=service_instance.memory_limit,
                                           memswap_limit=service_instance.memory_limit,
                                           name=service_instance.name,
                                           networks=[get_conf().overlay_network_name],
                                           network_disabled=False,
                                           network_mode=get_conf().overlay_network_name,
                                           ports=port_bindings,
                                           volumes=volumes)
        except docker.errors.ImageNotFound:
            raise ZoeException(message='Image not found')
        except docker.errors.APIError as e:
            if cont is not None:
                cont.remove(force=True)
            if e.explanation == b'no resources available to schedule container':
                raise ZoeNotEnoughResourcesException(message=e.explanation.decode('utf-8'))
            else:
                raise ZoeException(message=e.explanation.decode('utf-8'))
        except Exception as e:
            if cont is not None:
                cont.remove(force=True)
            raise ZoeException(str(e))

        cont = self.cli.containers.get(cont.id)
        return self._container_summary(cont)

    def _container_summary(self, container: docker.models.containers.Container):
        """Translate a docker-specific container object into a simple dictionary."""
        info = {
            "id": container.id,
            "ip_address": {},
            "name": container.name,
            'host': container.attrs['Node']['Name'],
            'labels': container.attrs['Config']['Labels']
        }  # type: Dict[str, Any]

        for net in container.attrs["NetworkSettings"]["Networks"]:
            if len(container.attrs["NetworkSettings"]["Networks"][net]['IPAddress']) > 0:
                info["ip_address"][net] = container.attrs["NetworkSettings"]["Networks"][net]['IPAddress']
            else:
                info["ip_address"][net] = None

        if container.status == 'running' or container.status == 'restarting':
            info["state"] = Service.BACKEND_START_STATUS
            info["running"] = True
        elif container.status == 'paused' or container.status == 'exited':
            info["state"] = Service.BACKEND_DIE_STATUS
            info["running"] = False
        elif container.status == 'OOMKilled':
            info["state"] = Service.BACKEND_OOM_STATUS
            info["running"] = False
        elif container.status == 'created':
            info["state"] = Service.BACKEND_CREATE_STATUS
            info["running"] = False
        else:
            log.error('Unknown container status: {}'.format(container.status))
            info["state"] = Service.BACKEND_UNDEFINED_STATUS
            info["running"] = False

        info['ports'] = {}
        if container.attrs['NetworkSettings']['Ports'] is not None:
            for port in container.attrs['NetworkSettings']['Ports']:
                if container.attrs['NetworkSettings']['Ports'][port] is not None:
                    mapping = (
                        container.attrs['NetworkSettings']['Ports'][port][0]['HostIp'],
                        container.attrs['NetworkSettings']['Ports'][port][0]['HostPort']
                    )
                    info['ports'][port] = mapping
                else:
                    info['ports'][port] = None

        return info

    def inspect_container(self, docker_id: str) -> Dict[str, Any]:
        """Retrieve information about a running container."""
        try:
            cont = self.cli.container.get(docker_id)
        except Exception as e:
            raise ZoeException(str(e))
        return self._container_summary(cont)

    def terminate_container(self, docker_id: str, delete=False) -> None:
        """
        Terminate a container.

        :param docker_id: The container to terminate
        :type docker_id: str
        :param delete: If True, also delete the container files
        :type delete: bool
        :return: None
        """
        try:
            cont = self.cli.containers.get(docker_id)
        except docker.errors.NotFound:
            return

        cont.stop(timeout=5)
        if delete:
            cont.remove(force=True)

    def event_listener(self, callback: Callable[[str], bool]) -> None:
        """An infinite loop that listens for events from Swarm."""
        event_gen = self.cli.events(decode=True)
        while True:
            try:
                event = next(event_gen)
            except requests.packages.urllib3.exceptions.ProtocolError:
                log.warning('Docker closed event connection, retrying...')
                event_gen = self.cli.events(decode=True)
                continue

            try:
                res = callback(event)
            except Exception:
                log.exception('Uncaught exception in swarm event callback')
                log.warning('event was: {}'.format(event))
                continue
            if not res:
                break

    def connect_to_network(self, container_id: str, network_id: str) -> None:
        """Connect a container to a network."""
        try:
            net = self.cli.networks.get(network_id)
        except docker.errors.NotFound:
            log.error('Trying to connect to a non-existent network')
            return
        net.connect(container_id)

    def disconnect_from_network(self, container_id: str, network_id: str) -> None:
        """Disconnects a container from a network."""
        try:
            net = self.cli.networks.get(network_id)
        except docker.errors.NotFound:
            log.error('Trying to connect to a non-existent network')
            return
        net.disconnect(container_id)

    def list(self, only_label=None) -> Iterable[dict]:
        """
        List running or defined containers.

        :param only_label: filter containers with only a certain label
        :return: a list of containers
        """
        try:
            ret = self.cli.containers.list(all=True)
        except docker.errors.APIError as ex:
            raise ZoeException(str(ex))
        conts = []
        for cont_info in ret:
            match = True
            for key, value in only_label.items():
                if key not in cont_info.attrs['Config']['Labels']:
                    match = False
                    break
                if cont_info.attrs['Config']['Labels'][key] != value:
                    match = False
                    break
            if match:
                conts.append(self._container_summary(cont_info))

        return conts

    def logs(self, docker_id: str, stream: bool, follow=None):
        """
        Retrieves the logs of the selected container.

        :param docker_id:
        :param stream:
        :param follow:
        :return:
        """
        try:
            cont = self.cli.containers.get(docker_id)
        except (docker.errors.NotFound, docker.errors.APIError):
            return None

        try:
            return cont.logs(docker_id, stdout=True, stderr=True, follow=follow, stream=stream, timestamps=True, tail='all')
        except docker.errors.APIError:
            return None
