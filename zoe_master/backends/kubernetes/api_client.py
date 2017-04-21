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
import logging
import json
import time
from argparse import Namespace

from typing import Dict, Any, List
import humanfriendly
import pykube

from zoe_master.stats import ClusterStats, NodeStats
from zoe_master.backends.service_instance import ServiceInstance
from zoe_lib.version import ZOE_VERSION
from zoe_lib.state import VolumeDescription

log = logging.getLogger(__name__)

ZOE_LABELS = {
    "app": "zoe",
    "version": ZOE_VERSION
}


class KubernetesConf:
    """Kubeconfig class"""
    def __init__(self, jsonfile):
        self.config = {}
        with open(jsonfile, 'r') as inp:
            self.config = json.load(inp)


class KubernetesServiceConf:
    """ Wrapper for Kubernetes Service configuration """
    def __init__(self):
        self.conf = {
            'kind': 'Service',
            'apiVersion': "v1",
            'metadata': {
                'labels': {}
            },
            'spec': {
                'selector': {},
                'type': 'LoadBalancer',
                'ports': []
            },
        }

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
        count = 0  # type: int

        for prt in ports:
            aux = self.conf['spec']['ports']  # type: List[Dict[str, str]]
            aux[count]['name'] = 'http'
            aux[count]['port'] = prt
            aux[count]['targetPort'] = prt
            count += 1

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
        self.conf = {
            'kind': 'ReplicationController',
            'apiVersion': "v1",
            'metadata': {
                'labels': {}
            },
            'spec': {
                'replicas': 1,
                'selector': {},
                'template': {
                    'metadata': {
                        'labels': {}
                    },
                    'spec': {
                        'containers': [{}]
                    }
                },
            }
        }

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
            aux = self.conf['spec']['template']  # type: Dict
            aux['metadata']['labels'][key] = lbs[key]

    def set_spec_container_image(self, image):
        """Setter to set container image"""
        aux = self.conf['spec']['template']  # type: Dict
        aux['spec']['containers'][0]['image'] = image

    def set_spec_container_name(self, name):
        """Setter to set container name"""
        aux = self.conf['spec']['template']  # type: Dict
        aux['spec']['containers'][0]['name'] = name

    def set_spec_container_env(self, env: dict):
        """Setter to set container environment"""
        aux = self.conf['spec']['template']  # type: Dict
        aux['spec']['containers'][0]['env'] = [{} for _ in range(len(env))]
        count = 0

        for k in env:
            aux['spec']['containers'][0]['env'][count]['name'] = k
            aux['spec']['containers'][0]['env'][count]['value'] = env[k]
            count += 1

    def set_spec_container_ports(self, ports):
        """Setter to set container ports"""
        aux = self.conf['spec']['template']  # type: Dict
        aux['spec']['containers'][0]['ports'] = [{} for _ in range(len(ports))]
        count = 0

        for prt in ports:
            aux['spec']['containers'][0]['ports'][count]['containerPort'] = prt
            count += 1

    def set_spec_container_mem_limit(self, memlimit):
        """Setter to set container mem limit"""
        memset = str(memlimit / (1024*1024)) + "Mi"
        aux = self.conf['spec']['template']  # type: Dict
        aux['spec']['containers'][0]['resources'] = {}
        aux['spec']['containers'][0]['resources']['limits'] = {}
        aux['spec']['containers'][0]['resources']['limits']['memory'] = memset

    def set_spec_container_core_limit(self, corelimit):
        """Setter to set container corelimit"""
        aux = self.conf['spec']['template']  # type: Dict
        aux['spec']['containers'][0]['resources']['limits']['cpu'] = corelimit

    def set_spec_container_volumes(self, volumes: List[VolumeDescription], name: str):
        """Setter to set container volumes"""
        aux = self.conf['spec']['template']  # type: Dict
        aux['spec']['containers'][0]['volumeMounts'] = [{} for _ in range(len(volumes))]
        count = 0

        for vol in volumes:
            if vol.type != "host_directory":
                log.error('Swarm backend does not support volume type {}'.format(vol.type))

            aux['spec']['containers'][0]['volumeMounts'][count]['mountPath'] = vol.mount_point
            aux['spec']['containers'][0]['volumeMounts'][count]['name'] = name + "-" + str(count)
            count += 1

        aux['spec']['volumes'] = [{} for _ in range(len(volumes))]
        count = 0

        for vol in volumes:
            aux['spec']['volumes'][count]['name'] = name + "-" + str(count)
            aux['spec']['volumes'][count]['hostPath'] = {
                'path': vol.path
            }
            count += 1

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

    def spawn_replication_controller(self, service_instance: ServiceInstance):
        """Create and start a new replication controller."""
        config = KubernetesReplicationControllerConf()
        config.set_name(service_instance.name)

        config.set_labels(ZOE_LABELS)
        config.set_labels({'service_name': service_instance.name})
        config.set_replicas(service_instance.replicas_count)

        config.set_spec_selector(ZOE_LABELS)
        config.set_spec_selector({'service_name': service_instance.name})

        config.set_temp_meta_labels(ZOE_LABELS)
        config.set_temp_meta_labels({'service_name': service_instance.name})

        config.set_spec_container_image(service_instance.image_name)
        config.set_spec_container_name(service_instance.name)

        if len(service_instance.environment) > 0:
            config.set_spec_container_env(service_instance.environment)

        if len(service_instance.ports) > 0:
            config.set_spec_container_ports(service_instance.ports)

        config.set_spec_container_mem_limit(service_instance.memory_limit)

        if service_instance.core_limit != 0:
            config.set_spec_container_core_limit(service_instance.core_limit)

        if len(service_instance.volumes) > 0:
            config.set_spec_container_volumes(service_instance.volumes, service_instance.name)

        info = {}

        try:
            pykube.ReplicationController(self.api, config.get_json()).create()
            log.info('Created ReplicationController on Kubernetes cluster')
            info = self.inspect_replication_controller(service_instance.name)
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
                "backend_id": rc_info['metadata']['uid'],
                'ip_address': '0.0.0.0'
            }

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
            if 0 < ready_replicas <= no_replicas:
                info['state'] = 'running'
                info['running'] = True
            else:
                info['state'] = 'undefined'
                info['running'] = True

        except pykube.exceptions.ObjectDoesNotExist:
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

    def spawn_service(self, service_instance: ServiceInstance):
        """Create and start a new Service object."""
        config = KubernetesServiceConf()

        config.set_name(service_instance.name)
        config.set_labels(ZOE_LABELS)
        config.set_labels({'service_name': service_instance.name})

        if len(service_instance.ports) > 0:
            config.set_ports(service_instance.ports)

        config.set_selectors(ZOE_LABELS)
        config.set_selectors({'service_name': service_instance.name})

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
                'port_forwarding': []  # type: List[Dict]
            }

            if 'clusterIP' in srv_info['spec']:
                info['clusterIP'] = srv_info['spec']['clusterIP']

            length = len(srv_info['spec']['ports'])

            info['port_forwarding'] = [{} for _ in range(length)]

            for i in range(length):  # type: int
                info['port_forwarding'][i]['port'] = srv_info['spec']['ports'][i]['port']
                info['port_forwarding'][i]['nodePort'] = srv_info['spec']['ports'][i]['nodePort']
        except Exception as ex:
            log.error(ex)
            info = None

        return info

    def terminate(self, name):
        """Terminate a service.
        It will terminate Service, then ReplicationController and Pods have the same labels."""
        del_obj = {
            'apiVersion': 'v1',
            'kind': '',
            'metadata': {
                'name': name
            }
        }
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

    def info(self) -> ClusterStats:  # pylint: disable=too-many-locals
        """Retrieve Kubernetes cluster statistics."""
        pl_status = ClusterStats()

        node_list = pykube.Node.objects(self.api).iterator()
        node_dict = {}

        # Get basic information from nodes
        for node in node_list:
            nss = NodeStats(node.name)
            nss.cores_total = float(node.obj['status']['allocatable']['cpu'])
            nss.memory_total = humanfriendly.parse_size(node.obj['status']['allocatable']['memory'])
            nss.labels = node.obj['metadata']['labels']
            node_dict[node.name] = nss

        # Get information from all running pods, then accumulate to nodes
        pod_list = pykube.Pod.objects(self.api).filter(namespace=pykube.all).iterator()
        for pod in pod_list:
            host_ip = pod.obj['status']['hostIP']
            nss = node_dict[host_ip]
            nss.container_count += 1
            spec_cont = pod.obj['spec']['containers'][0]
            if 'resources' in spec_cont:
                if 'requests' in spec_cont['resources']:
                    if 'memory' in spec_cont['resources']['requests']:
                        memory = spec_cont['resources']['requests']['memory']
                        nss.memory_reserved = nss.memory_reserved + humanfriendly.parse_size(memory)
                    if 'cpu' in spec_cont['resources']['requests']:
                        cpu = spec_cont['resources']['requests']['cpu']
                        # ex: cpu could be 100m or 0.1
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
