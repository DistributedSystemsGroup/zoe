# Copyright (c) 2016, Quang-Nhat Hoang-Xuan
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

"""Interface to the low-level Kubernetes API."""

try:
    import pykube
except ImportError:
    pykube = None

from argparse import Namespace
from typing import Iterable, Dict, Any, Union

import logging
import json
import time
import humanfriendly

from zoe_master.stats import ClusterStats, NodeStats
from zoe_lib.version import ZOE_VERSION

log = logging.getLogger(__name__)

ZOE_LABELS = {"app": "zoe", "version": ZOE_VERSION}

class DockerContainerOptions:
    """Wrapper for the Docker container options."""
    def __init__(self):
        self.env = {}
        self.volume_binds = []
        self.volumes = []
        self.command = ""
        self.memory_limit = 2 * (1024**3)
        self.cores_limit = 0
        self.name = ''
        self.ports = []
        self.network_name = 'bridge'
        self.restart = True
        self.labels = []
        self.gelf_log_address = ''
        self.constraints = []
        self.replicas = 1

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

    def set_command(self, cmd):
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

    def set_cores_limit(self, limit: float):
        """Setter for the cores limit of the container."""
        self.cores_limit = limit

    def get_cores_limit(self):
        """Getter for the cores limit of the container."""
        return self.cores_limit

    @property
    def restart_policy(self) -> Dict[str, str]:
        """Getter for the restart policy of the container."""
        if self.restart:
            return {'Name': 'always'}
        else:
            return {}

    def set_replicas(self, reps: int):
        """Setter to set replicas"""
        self.replicas = reps

    def get_replicas(self) -> int:
        """Getter to get replicas"""
        return self.replicas

class KubernetesConf:
    """Kubeconfig class"""
    def __init__(self, jsonfile):
        self.config = {}
        with open(jsonfile, 'r') as inp:
            self.config = json.load(inp)

class KubernetesServiceConf:
    """ Wrapper for Kubernetes Service configuration """
    def __init__(self):
        self.conf = {}
        self.conf['kind'] = 'Service'
        self.conf['apiVersion'] = "v1"
        self.conf['metadata'] = {}
        self.conf['metadata']['labels'] = {}
        self.conf['spec'] = {}
        self.conf['spec']['selector'] = {}
        self.conf['spec']['type'] = 'LoadBalancer'

    def set_name(self, name):
        """Setter to set name"""
        self.conf['metadata']['name'] = name

    def set_labels(self, lbs: dict):
        """Setter to set label"""
        for key in lbs:
            self.conf['metadata']['labels'][key] = lbs[key]

    def set_ports(self, ports):
        """Setter to set ports"""
        self.conf['spec']['ports'] = [{} for _ in range(len(ports))]
        count = 0

        for prt in ports:
            self.conf['spec']['ports'][count]['name'] = 'http'
            self.conf['spec']['ports'][count]['port'] = prt
            self.conf['spec']['ports'][count]['targetPort'] = prt
            count = count + 1

    def set_selectors(self, selectors: dict):
        """Setter to set selectors"""
        for key in selectors:
            self.conf['spec']['selector'][key] = selectors[key]

    def get_json(self):
        """get Json files"""
        return self.conf

class KubernetesReplicationControllerConf:
    """ Wrapper for Kubernetes ReplicationController Configuration """
    def __init__(self):
        self.conf = {}
        self.conf['kind'] = 'ReplicationController'
        self.conf['apiVersion'] = "v1"
        self.conf['metadata'] = {}
        self.conf['metadata']['labels'] = {}

        self.conf['spec'] = {}

        self.conf['spec']['replicas'] = 1

        self.conf['spec']['selector'] = {}

        self.conf['spec']['template'] = {}
        self.conf['spec']['template']['metadata'] = {}
        self.conf['spec']['template']['metadata']['labels'] = {}

        self.conf['spec']['template']['spec'] = {}
        self.conf['spec']['template']['spec']['containers'] = [{}]

    def set_name(self, name):
        """Setter to set name"""
        self.conf['metadata']['name'] = name

    def set_labels(self, lbs: dict):
        """Setter to set label"""
        for key in lbs:
            self.conf['metadata']['labels'][key] = lbs[key]

    def set_replicas(self, reps):
        """Setter to set replicas"""
        self.conf['spec']['replicas'] = reps

    def set_spec_selector(self, lbs: dict):
        """Setter to set specselector"""
        for key in lbs:
            self.conf['spec']['selector'][key] = lbs[key]

    def set_temp_meta_labels(self, lbs: dict):
        """Setter to set spectemplatemetadatalabel"""
        for key in lbs:
            self.conf['spec']['template']['metadata']['labels'][key] = lbs[key]

    def set_spec_container_image(self, image):
        """Setter to set container image"""
        self.conf['spec']['template']['spec']['containers'][0]['image'] = image

    def set_spec_container_name(self, name):
        """Setter to set container name"""
        self.conf['spec']['template']['spec']['containers'][0]['name'] = name

    def set_spec_container_env(self, env: dict):
        """Setter to set container environment"""
        self.conf['spec']['template']['spec']['containers'][0]['env'] = [{} for _ in range(len(env))]
        count = 0

        for k in env:
            self.conf['spec']['template']['spec']['containers'][0]['env'][count]['name'] = k
            self.conf['spec']['template']['spec']['containers'][0]['env'][count]['value'] = env[k]
            count = count + 1

    def set_spec_container_ports(self, ports):
        """Setter to set container ports"""
        self.conf['spec']['template']['spec']['containers'][0]['ports'] = [{} for _ in range(len(ports))]
        count = 0

        for prt in ports:
            self.conf['spec']['template']['spec']['containers'][0]['ports'][count]['containerPort'] = prt
            count = count + 1

    def set_spec_container_mem_limit(self, memlimit):
        """Setter to set container mem limit"""
        memset = str(memlimit / (1024*1024)) + "Mi"
        self.conf['spec']['template']['spec']['containers'][0]['resources'] = {}
        self.conf['spec']['template']['spec']['containers'][0]['resources']['limits'] = {}
        self.conf['spec']['template']['spec']['containers'][0]['resources']['limits']['memory'] = memset

    def set_spec_container_core_limit(self, corelimit):
        """Setter to set container corelimit"""
        self.conf['spec']['template']['spec']['containers'][0]['resources']['limits']['cpu'] = corelimit

    def set_spec_container_volumes(self, volumes, name):
        """Setter to set container volumes"""
        self.conf['spec']['template']['spec']['containers'][0]['volumeMounts'] = [{} for _ in range(len(volumes))]
        count = 0

        for vol in volumes:
            vsplit = vol.split(':')
            self.conf['spec']['template']['spec']['containers'][0]['volumeMounts'][count]['mountPath'] = vsplit[0]
            self.conf['spec']['template']['spec']['containers'][0]['volumeMounts'][count]['name'] = name + "-" + str(count)
            count = count + 1

        self.conf['spec']['template']['spec']['volumes'] = [{} for _ in range(len(volumes))]
        count = 0

        for vol in volumes:
            vsplit = vol.split(':')
            self.conf['spec']['template']['spec']['volumes'][count]['name'] = name + "-" + str(count)
            self.conf['spec']['template']['spec']['volumes'][count]['hostPath'] = {}
            self.conf['spec']['template']['spec']['volumes'][count]['hostPath']['path'] = vsplit[1]
            count = count + 1

    def get_json(self):
        """Get json file"""
        return self.conf

class KubernetesClient:
    """The Kubernetes client class that wraps the Kubernetes API."""
    def __init__(self, opts: Namespace) -> None:
        #try:
        self.api = pykube.HTTPClient(pykube.KubeConfig.from_file(opts.kube_config_file))
        #except Exception as e:
        #    log.error(e)

    def spawn_replication_controller(self, image: str, options: DockerContainerOptions):
        """Create and start a new replication controller."""
        config = KubernetesReplicationControllerConf()
        config.set_name(options.name)

        config.set_labels(ZOE_LABELS)
        config.set_labels({'service_name' : options.name})
        config.set_replicas(options.get_replicas())

        config.set_spec_selector(ZOE_LABELS)
        config.set_spec_selector({'service_name' : options.name})

        config.set_temp_meta_labels(ZOE_LABELS)
        config.set_temp_meta_labels({'service_name': options.name})

        config.set_spec_container_image(image)
        config.set_spec_container_name(options.name)

        if len(options.environment) > 0:
            config.set_spec_container_env(options.environment)

        if len(options.ports) > 0:
            config.set_spec_container_ports(options.ports)

        config.set_spec_container_mem_limit(options.get_memory_limit())

        if options.get_cores_limit() != 0:
            config.set_spec_container_core_limit(options.get_cores_limit())

        if len(list(options.get_volume_binds())) > 0:
            config.set_spec_container_volumes(list(options.get_volume_binds()), options.name)

        info = {}

        try:
            pykube.ReplicationController(self.api, config.get_json()).create()
            log.info('Created ReplicationController on Kubernetes cluster')
            info = self.inspect_replication_controller(options.name)
        except Exception as ex:
            log.error(ex)

        return info

    def inspect_replication_controller(self, name):
        """Get information about a specific replication controller."""
        try:
            repcon_list = pykube.ReplicationController.objects(self.api)
            rep = repcon_list.get_by_name(name)
            rc_info = rep.obj

            info = {
                "backend_id": rc_info['metadata']['uid']
            }

            info['ip_address'] = '0.0.0.0'

            no_replicas = rc_info['spec']['replicas']

            if 'readyReplicas' in rc_info['status']:
                ready_replicas = rc_info['status']['readyReplicas']
            else:
                ready_replicas = 0

            info['replicas'] = no_replicas
            info['readyReplicas'] = ready_replicas

            if ready_replicas <= 0:
                info['state'] = 'undefined'
                info['running'] = False
            if ready_replicas > 0 and ready_replicas <= no_replicas:
                info['state'] = 'running'
                info['running'] = True
            else:
                info['state'] = 'undefined'
                info['running'] = True

        except pykube.exceptions.ObjectDoesNotExist as ex:
            return None
        except Exception as ex:
            log.error(ex)
            return None

        return info

    def replication_controller_list(self):
        """Get list of replication controller."""
        repcon_list = pykube.ReplicationController.objects(self.api).filter(selector=ZOE_LABELS).iterator()
        rclist = []
        try:
            for rep in repcon_list:
                rclist.append(self.inspect_replication_controller(rep.name))
        except Exception as ex:
            log.error(ex)
        return rclist

    def replication_controller_event(self):
        """Get event stream of the replication controller."""
        rc_stream = pykube.ReplicationController.objects(self.api).filter(selector=ZOE_LABELS).watch()
        return rc_stream

    def spawn_service(self, options: DockerContainerOptions):
        """Create and start a new Service object."""
        config = KubernetesServiceConf()

        config.set_name(options.name)
        config.set_labels(ZOE_LABELS)
        config.set_labels({'service_name' : options.name})

        if len(options.ports) > 0:
            config.set_ports(options.ports)

        config.set_selectors(ZOE_LABELS)
        config.set_selectors({'service_name' : options.name})

        try:
            pykube.Service(self.api, config.get_json()).create()
            log.info('created service on Kubernetes cluster')
        except Exception as ex:
            log.error(ex)
        return

    def inspect_service(self, name) -> Dict[str, Any]:
        """Get information of a specific service."""
        try:
            service_list = pykube.Service.objects(self.api)
            service = service_list.get_by_name(name)
            srv_info = service.obj

            info = {
                'service_name': name,
                'port_forwarding': []
            }

            if 'clusterIP' in srv_info['spec']:
                info['clusterIP'] = srv_info['spec']['clusterIP']

            lgth = len(srv_info['spec']['ports'])

            info['port_forwarding'] = [{} for _ in range(lgth)]

            for i in range(lgth):
                info['port_forwarding'][i]['port'] = srv_info['spec']['ports'][i]['port']
                info['port_forwarding'][i]['nodePort'] = srv_info['spec']['ports'][i]['nodePort']
        except Exception as ex:
            log.error(ex)

        return info

    def terminate(self, name):
        """Terminate a service.
        It will terminate Service, then ReplicationController and Pods have the same labels."""
        del_obj = {'apiVersion': 'v1', 'kind': '', 'metadata' : {'name' : name}}
        try:
            del_obj['kind'] = 'Service'
            pykube.Service(self.api, del_obj).delete()

            del_obj['kind'] = 'ReplicationController'
            pykube.ReplicationController(self.api, del_obj).delete()

            del_obj['kind'] = 'Pod'
            pod_selector = ZOE_LABELS
            pod_selector['service_name'] = name
            pods = pykube.Pod.objects(self.api).filter(namespace="default", selector=pod_selector).iterator()
            for pod in pods:
                del_obj['metadata']['name'] = str(pod)
                pykube.Pod(self.api, del_obj).delete()

            log.info('Service deleted on Kubernetes cluster')
        except Exception as ex:
            log.error(ex)

    def info(self) -> ClusterStats: #pylint: disable=too-many-locals
        """Retrieve Kubernetes cluster statistics."""
        pl_status = ClusterStats()

        node_list = pykube.Node.objects(self.api).iterator()
        node_dict = {}

        #Get basic information from nodes
        for node in node_list:
            nss = NodeStats(node.name)
            nss.cores_total = float(node.obj['status']['allocatable']['cpu'])
            nss.memory_total = humanfriendly.parse_size(node.obj['status']['allocatable']['memory'])
            nss.labels = node.obj['metadata']['labels']
            node_dict[node.name] = nss

        #Get information from all running pods, then accummulate to nodes
        pod_list = pykube.Pod.objects(self.api).filter(namespace=pykube.all).iterator()
        for pod in pod_list:
            host_ip = pod.obj['status']['hostIP']
            nss = node_dict[host_ip]
            nss.container_count = nss.container_count + 1
            spec_cont = pod.obj['spec']['containers'][0]
            if 'resources' in spec_cont:
                if 'requests' in spec_cont['resources']:
                    if 'memory' in spec_cont['resources']['requests']:
                        memory = spec_cont['resources']['requests']['memory']
                        nss.memory_reserved = nss.memory_reserved + humanfriendly.parse_size(memory)
                    if 'cpu' in spec_cont['resources']['requests']:
                        cpu = spec_cont['resources']['requests']['cpu']
                        #ex: cpu could be 100m or 0.1
                        cpu_splitted = cpu.split('m')
                        if len(cpu_splitted) > 1:
                            cpu_float = int(cpu_splitted[0]) / 1000
                        else:
                            cpu_float = int(cpu_splitted[0])
                        nss.cores_reserved = round(nss.cores_reserved + cpu_float, 3)

        cont_total = 0
        mem_total = 0
        cpu_total = 0

        for node_ip in node_dict:
            pl_status.nodes.append(node_dict[node_ip])
            cont_total = cont_total + node_dict[node_ip].container_count
            mem_total = mem_total + node_dict[node_ip].memory_total
            cpu_total = cpu_total + node_dict[node_ip].cores_total

        pl_status.container_count = cont_total
        pl_status.memory_total = mem_total
        pl_status.cores_total = cpu_total
        pl_status.timestamp = time.time()

        return pl_status
