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

import operator
import logging
import json
import time
import humanfriendly

from typing import Iterable, Callable, Dict, Any, Union

from zoe_master.stats import ClusterStats, NodeStats

from argparse import Namespace
from typing import Dict, Any

log = logging.getLogger(__name__)

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
        self.replicas = reps

    def get_replicas(self) -> int:
        return self.replicas

class KubernetesConf:
    def __init__(self, jsonfile):
        self.config = {}
        with open(jsonfile, 'r') as f:
            self.config = json.load(f)

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

    def setName(self, name):
        self.conf['metadata']['name'] = name

    def setLabels(self, lb: dict):
        for k in lb:
            self.conf['metadata']['labels'][k] = lb[k]

    def setPorts(self, ports):
        self.conf['spec']['ports'] = [{} for _ in range(len(ports))]
        count = 0

        for p in ports:
            self.conf['spec']['ports'][count]['name'] = 'http'
            self.conf['spec']['ports'][count]['port'] = p
            self.conf['spec']['ports'][count]['targetPort'] = p
            count = count + 1

    def setSelectors(self, selectors: dict):
        for k in selectors:
            self.conf['spec']['selector'][k] = selectors[k]

    def getJson(self):
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

    def setName(self, name):
        self.conf['metadata']['name'] = name

    def setLabels(self, lb: dict):
        for k in lb:
            self.conf['metadata']['labels'][k] = lb[k]

    def setReplicas(self, reps):
        self.conf['spec']['replicas'] = reps

    def setSpecSelector(self, lb: dict):
        for k in lb:
            self.conf['spec']['selector'][k] = lb[k]

    def setSpecTemplateMetadataLabels(self, lb: dict):
        for k in lb:
            self.conf['spec']['template']['metadata']['labels'][k] = lb[k]

    def setSpecTemplateSpecContainerImage(self, image):
        self.conf['spec']['template']['spec']['containers'][0]['image'] = image

    def setSpecTemplateSpecContainerName(self, name):
        self.conf['spec']['template']['spec']['containers'][0]['name'] = name

    def setSpecTemplateSpecContainerEnv(self, env: dict):
        self.conf['spec']['template']['spec']['containers'][0]['env'] = [{} for _ in range(len(env))]
        count = 0

        for k in env:
            self.conf['spec']['template']['spec']['containers'][0]['env'][count]['name'] = k
            self.conf['spec']['template']['spec']['containers'][0]['env'][count]['value'] = env[k]
            count = count + 1

    def setSpecTemplateSpecContainerPorts(self, ports):
        self.conf['spec']['template']['spec']['containers'][0]['ports'] = [{} for _ in range(len(ports))]
        count = 0

        for p in ports:
            self.conf['spec']['template']['spec']['containers'][0]['ports'][count]['containerPort'] = p
            count = count + 1

    def setSpecTemplateSpecContainerMemLimit(self, memlimit):
        memset = str(memlimit / (1024*1024)) + "Mi"
        self.conf['spec']['template']['spec']['containers'][0]['resources'] = {}
        self.conf['spec']['template']['spec']['containers'][0]['resources']['limits'] = {}
        self.conf['spec']['template']['spec']['containers'][0]['resources']['limits']['memory'] = memset

    def setSpecTemplateSpecContainerCoreLimit(self, corelimit):
        self.conf['spec']['template']['spec']['containers'][0]['resources']['limits']['cpu'] = corelimit

    def setSpecTemplateSpecContainerVolumes(self, volumes, name):
        self.conf['spec']['template']['spec']['containers'][0]['volumeMounts'] = [{} for _ in range(len(volumes))]
        count = 0

        for v in volumes:
            vsplit = v.split(':')
            self.conf['spec']['template']['spec']['containers'][0]['volumeMounts'][count]['mountPath'] = vsplit[0]
            self.conf['spec']['template']['spec']['containers'][0]['volumeMounts'][count]['name'] = name + "-" + str(count)
            count = count + 1

        self.conf['spec']['template']['spec']['volumes'] = [{} for _ in range(len(volumes))]
        count = 0

        for v in volumes:
            vsplit = v.split(':')
            self.conf['spec']['template']['spec']['volumes'][count]['name'] = name + "-" + str(count)
            self.conf['spec']['template']['spec']['volumes'][count]['hostPath'] = {}
            self.conf['spec']['template']['spec']['volumes'][count]['hostPath']['path'] = vsplit[1]
            count = count + 1

    def getJson(self):
        return self.conf

class KubernetesClient:
    """The Kubernetes client class that wraps the Kubernetes API."""
    def __init__(self, opts: Namespace) -> None:
        try:
            self.api = pykube.HTTPClient(pykube.KubeConfig.from_file(opts.kube_config_file))
        except Exception as e:
            log.error(e)

    def spawn_replication_controller(self, image: str, options: DockerContainerOptions):
        """Create and start a new replication controller."""
        config = KubernetesReplicationControllerConf()
        config.setName(options.name)

        config.setLabels({'service_name' : options.name, 'app': 'zoe'})
        config.setReplicas(options.get_replicas())
        
        config.setSpecSelector({'service_name' : options.name, 'app': 'zoe'})
        config.setSpecTemplateMetadataLabels({'service_name': options.name, 'app': 'zoe'})

        config.setSpecTemplateSpecContainerImage(image)
        config.setSpecTemplateSpecContainerName(options.name)

        if len(options.environment) > 0:
            config.setSpecTemplateSpecContainerEnv(options.environment)

        if len(options.ports) > 0:
            config.setSpecTemplateSpecContainerPorts(options.ports)

        config.setSpecTemplateSpecContainerMemLimit(options.get_memory_limit())
        
        if options.get_cores_limit() != 0:
            config.setSpecTemplateSpecContainerCoreLimit(options.get_cores_limit())

        if len(list(options.get_volume_binds())) > 0:
            config.setSpecTemplateSpecContainerVolumes(list(options.get_volume_binds()), options.name)

        info = {}

        try:
            pykube.ReplicationController(self.api, config.getJson()).create()
            log.info('Created ReplicationController on Kubernetes cluster')
            info = self.inspect_replication_controller(options.name)
        except Exception as ex:
            log.error(ex)

        return info

    def inspect_replication_controller(self, name):
        """Get information about a specific replication controller."""
        try:
            repconList = pykube.ReplicationController.objects(self.api)
            rc = repconList.get_by_name(name)
            rc_info = rc.obj

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

            if ready_replicas <=0 :
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
        repconList = pykube.ReplicationController.objects(self.api).filter(selector={"app":"zoe"}).iterator()
        rclist = []
        try:
            for rc in repconList:
                rclist.append(self.inspect_replication_controller(rc.name))
        except Exception as ex:
            log.error(ex)
        return rclist
                    

    def replication_controller_event(self):
        """Get event stream of the replication controller."""
        rcStream =  pykube.ReplicationController.objects(self.api).filter(selector={"app":"zoe"}).watch()
        return rcStream

    def spawn_service(self, image: str, options: DockerContainerOptions):
        """Create and start a new Service object."""
        config = KubernetesServiceConf()

        config.setName(options.name)
        config.setLabels({'service_name' : options.name, 'app' : 'zoe'})

        if len(options.ports) > 0:
            config.setPorts(options.ports)

        config.setSelectors({'service_name' : options.name, 'app' : 'zoe'})

        try:
            pykube.Service(self.api, config.getJson()).create()
            log.info('created service on Kubernetes cluster')
        except Exception as ex:
            log.error(ex)
        return

    def inspect_service(self, name) -> Dict[str, Any]:
        """Get information of a specific service."""
        try:
            srvList = pykube.Service.objects(self.api)
            service = srvList.get_by_name(name)
            srv_info = service.obj

            info = {
                'service_name': name,
                'port_forwarding': []
            }

            if 'clusterIP' in srv_info['spec']:
                info['clusterIP'] = srv_info['spec']['clusterIP']

            l = len(srv_info['spec']['ports'])

            info['port_forwarding'] = [{} for _ in range(l)]

            for i in range(l):
                info['port_forwarding'][i]['port'] = srv_info['spec']['ports'][i]['port']
                info['port_forwarding'][i]['nodePort'] = srv_info['spec']['ports'][i]['nodePort']
        except Exception as ex:
            log.error(ex)

        return info

    def terminate(self, name):
        """Terminate a service.
        It will terminate Service, then ReplicationController and Pods have the same labels."""
        delObj = {'apiVersion': 'v1', 'kind': '', 'metadata' : {'name' : name}}
        try:
            delObj['kind'] = 'Service'
            pykube.Service(self.api, delObj).delete()

            delObj['kind'] = 'ReplicationController' 
            pykube.ReplicationController(self.api, delObj).delete()

            delObj['kind'] = 'Pod'
            pods = pykube.Pod.objects(self.api).filter(namespace="default", selector={"service_name": name, "app": "zoe"}).iterator()
            for p in pods:
                delObj['metadata']['name'] = str(p)
                pykube.Pod(self.api, delObj).delete()

            log.info('Service deleted on Kubernetes cluster')
        except Exception as ex:
            log.error(ex)

    def info(self) -> ClusterStats:
        """Retrieve Kubernetes cluster statistics."""
        pl_status = ClusterStats()
        
        nodeList = pykube.Node.objects(self.api).iterator()
        nodeDict = {}

        #Get basic information from nodes
        for node in nodeList:
            ns = NodeStats(node.name)
            ns.cores_total = float(node.obj['status']['allocatable']['cpu'])
            ns.memory_total = humanfriendly.parse_size(node.obj['status']['allocatable']['memory'])
            ns.labels = node.obj['metadata']['labels']
            nodeDict[node.name] = ns
        
        #Get information from all running pods, then accummulate to nodes
        podList = pykube.Pod.objects(self.api).filter(namespace=pykube.all).iterator()
        for pod in podList:
            hostIP = pod.obj['status']['hostIP']
            ns = nodeDict[hostIP]
            ns.container_count = ns.container_count + 1
            specCont = pod.obj['spec']['containers'][0]
            if 'resources' in specCont:
                if 'requests' in specCont['resources']:
                    if 'memory' in specCont['resources']['requests']:
                        memory = specCont['resources']['requests']['memory']
                        ns.memory_reserved = ns.memory_reserved + humanfriendly.parse_size(memory)
                    if 'cpu' in specCont['resources']['requests']:
                        cpu = specCont['resources']['requests']['cpu']
                        #ex: cpu could be 100m or 0.1
                        cpu_splitted = cpu.split('m')
                        if len(cpu_splitted) > 1:
                            cpu_float = int(cpu_splitted[0]) / 1000
                        else:
                            cpu_float = int(cpu_splitted[0])
                        ns.cores_reserved = round(ns.cores_reserved + cpu_float, 3)

        contTotal = 0
        memTotal = 0
        cpuTotal = 0
        
        for nodeIP in nodeDict:
            pl_status.nodes.append(nodeDict[nodeIP])
            contTotal = contTotal + nodeDict[nodeIP].container_count
            memTotal = memTotal + nodeDict[nodeIP].memory_total
            cpuTotal = cpuTotal + nodeDict[nodeIP].cores_total

        pl_status.container_count = contTotal
        pl_status.memory_total = memTotal
        pl_status.cores_total = cpuTotal
        pl_status.timestamp = time.time()

        return pl_status

