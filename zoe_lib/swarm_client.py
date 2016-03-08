# Copyright (c) 2015, Daniele Venzano
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

import time
import logging

import humanfriendly
import requests.exceptions

try:
    from kazoo.client import KazooClient
except ImportError:
    KazooClient = None

import docker
import docker.errors

from zoe_scheduler.stats import SwarmStats, SwarmNodeStats, ContainerStats
from zoe_lib.exceptions import ZoeException

log = logging.getLogger(__name__)


def zookeeper_swarm(zk_server_list: str, path='/docker'):
    """
    Given a Zookeeper server list, find the currently active Swarm master.
    :param zk_server_list: Zookeeper server list
    :param path: Swarm path in Zookeeper
    :return: Swarm master connection string
    """
    path += '/docker/swarm/leader'
    zk = KazooClient(hosts=zk_server_list)
    zk.start()
    master, stat = zk.get(path)
    zk.stop()
    return master


class SwarmClient:
    def __init__(self, opts):
        self.opts = opts
        url = opts.swarm
        if 'zk://' in url:
            url = url[len('zk://'):]
            manager = zookeeper_swarm(url)
            manager = manager.decode('utf-8')
        elif 'http://' or 'https://' in url:
            manager = url
        else:
            raise ZoeException('Unsupported URL scheme for Swarm')
        log.info('Connecting to Swarm at {}'.format(manager))
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
            idx2 = 0
            ns = SwarmNodeStats(info["DriverStatus"][idx + node][0])
            ns.docker_endpoint = info["DriverStatus"][idx + node][1]
            idx2 += 1
            ns.status = info["DriverStatus"][idx + node + idx2][1]
            idx2 += 1
            ns.container_count = int(info["DriverStatus"][idx + node + idx2][1])
            idx2 += 1
            ns.cores_reserved = int(info["DriverStatus"][idx + node + idx2][1].split(' / ')[0])
            ns.cores_total = int(info["DriverStatus"][idx + node + idx2][1].split(' / ')[1])
            idx2 += 1
            ns.memory_reserved = info["DriverStatus"][idx + node + idx2][1].split(' / ')[0]
            ns.memory_total = info["DriverStatus"][idx + node + idx2][1].split(' / ')[1]
            idx2 += 1
            ns.labels = info["DriverStatus"][idx + node + idx2][1:]
            idx2 += 1
            ns.error = info["DriverStatus"][idx + node + idx2][1]
            idx2 += 1
            ns.last_update = info["DriverStatus"][idx + node + idx2][1]

            ns.memory_reserved = humanfriendly.parse_size(ns.memory_reserved)
            ns.memory_total = humanfriendly.parse_size(ns.memory_total)

            pl_status.nodes.append(ns)
            idx += idx2
        pl_status.timestamp = time.time()
        return pl_status

    def spawn_container(self, image, options) -> dict:
        cont = None
        port_bindings = {}
        for port in options.ports:
            port_bindings[port] = None

        try:
            host_config = self.cli.create_host_config(network_mode=options.network_name,
                                                      binds=options.get_volume_binds(),
                                                      mem_limit=options.get_memory_limit(),
                                                      memswap_limit=options.get_memory_limit(),
                                                      restart_policy=options.restart_policy,
                                                      port_bindings=port_bindings)
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
        except docker.errors.APIError as e:
            if cont is not None:
                self.cli.remove_container(container=cont.get('Id'), force=True)
            raise ZoeException(e.explanation.decode('utf-8'))
        except requests.exceptions.ConnectionError:
            if cont is not None:
                self.cli.remove_container(container=cont.get('Id'), force=True)
            raise ZoeException('Connection error while creating the container')
        info = self.inspect_container(cont.get('Id'))
        return info

    def inspect_container(self, docker_id) -> dict:
        try:
            docker_info = self.cli.inspect_container(container=docker_id)
        except docker.errors.APIError:
            return None
        info = {
            "docker_id": docker_id,
            "ip_address": {}
        }
        for net in docker_info["NetworkSettings"]["Networks"]:
            info["ip_address"][net] = docker_info["NetworkSettings"]["Networks"][net]['IPAddress']

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

    def terminate_container(self, docker_id, delete=False):
        if delete:
            try:
                self.cli.remove_container(docker_id, force=True)
            except docker.errors.NotFound:
                log.warning("cannot remove a non-existent container")
        else:
            try:
                self.cli.kill(docker_id)
            except docker.errors.NotFound:
                log.warning("cannot remove a non-existent container")

    def log_get(self, docker_id) -> str:
        try:
            logdata = self.cli.logs(container=docker_id, stdout=True, stderr=True, stream=False, timestamps=False, tail="all")
        except docker.errors.NotFound:
            return None
        return logdata.decode("utf-8")

    def stats(self, docker_id) -> ContainerStats:
        stats_stream = self.cli.stats(docker_id, decode=True)
        for s in stats_stream:
            return ContainerStats(s)

    def event_listener(self, callback):
        for event in self.cli.events(decode=True):
            if not callback(event):
                break

    def network_create(self, name: str) -> str:
        ret = self.cli.create_network(name, driver='overlay')
        return ret['Id']

    def network_remove(self, nid):
        try:
            self.cli.remove_network(nid)
        except docker.errors.APIError:
            log.exception('cannot remove network "{}"'.format(nid))

    def network_list(self, search=''):
        all_nets = self.cli.networks()
        ret = []
        for net in all_nets:
            if search in net['Name']:
                n = {
                    'id': net['Id'],
                    'name': net['Name']
                }
                ret.append(n)
        return ret

    def connect_to_network(self, container_id, network_id):
        try:
            self.cli.connect_container_to_network(container_id, network_id)
        except docker.errors.APIError:
            log.exception('cannot connect container {} to network {}'.format(container_id, network_id))

    def disconnect_from_network(self, container_id, network_id):
        try:
            self.cli.disconnect_container_from_network(container_id, network_id)
        except docker.errors.APIError:
            log.exception('cannot disconnect container {} from network {}'.format(container_id, network_id))

    def list(self, only_label=None) -> list:
        if only_label is None:
            filters = {}
        else:
            filters = {
                'label': only_label
            }
        ret = self.cli.containers(all=True, filters=filters)
        conts = []
        for c in ret:
            aux = c['Names'][0].split('/')  # Swarm returns container names in the form /host/name
            conts.append({
                'id': c['Id'],
                'host': aux[1],
                'name': aux[2],
                'labels': c['Labels'],
                'status': c['Status']
            })
        return conts


class ContainerOptions:
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

    def add_env_variable(self, name, value):
        if value is not None:
            self.env[name] = value

    @property
    def environment(self):
        return self.env

    def add_volume_bind(self, path, mountpoint, readonly=False):
        self.volumes.append(mountpoint)
        self.volume_binds.append(path + ":" + mountpoint + ":" + ("ro" if readonly else "rw"))

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

    @property
    def restart_policy(self):
        if self.restart:
            return {'Name': 'always'}
        else:
            return {}
