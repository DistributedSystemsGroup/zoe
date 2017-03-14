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

"""Proxifying using Apache2 Container."""

import docker
import time
import logging
import random

import zoe_api.proxy.base
import zoe_api.api_endpoint
from zoe_master.backends.old_swarm.api_client import SwarmClient
from zoe_master.backends.kubernetes.api_client import KubernetesClient
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)

class ApacheProxy(zoe_api.proxy.base.BaseProxy):
    """Apache proxy class."""
    def __init__(self, apiEndpoint):
        self.api_endpoint = apiEndpoint

    """Proxify function."""
    def proxify(self, uid, role, id):
        try:
            length_service = 0
            
            #Wait until all the services get created and started to be able to get the backend_id
            while self.api_endpoint.execution_by_id(uid, role, id).status != 'running':
                log.info('Waiting for all services get started...')
                length_service = len(self.api_endpoint.execution_by_id(uid, role, id).services)
                time.sleep(1)

            exe = self.api_endpoint.execution_by_id(uid, role, id)
            l = len(exe.services)
            
            while l != 0:
                exe = self.api_endpoint.execution_by_id(uid, role, id)
                l = len(exe.services)
                for srv in exe.services:
                    if srv.backend_id == None:
                        time.sleep(1)
                    else:
                        l = l - 1 
            
            #Start proxifying by adding entry to use proxypass and proxypassreverse in apache2 config file
            for srv in exe.services:
                ip, p = None, None

                if get_conf().backend == 'OldSwarm':
                    swarm = SwarmClient(get_conf())
                    s_info = swarm.inspect_container(srv.backend_id)
                    portList = s_info['ports']

                    for k,v in portList.items():
                        exposedPort = k.split('/tcp')[0]
                        if v != None:
                            ip = v[0]
                            p = v[1]
                        
                        base_path = '/zoe/' + uid + '/' + str(id) + '/' + srv.name + '/' + exposedPort
                        original_path = str(ip) + ':' + str(p) + base_path
                                        
                        if ip is not None and p is not None:
                            log.info('Proxifying %s', srv.name + ' port ' + exposedPort)
                            self.dispatch_to_docker(base_path, original_path)
                else:
                    kube = KubernetesClient(get_conf())
                    s_info = kube.inspect_service(srv.dns_name)
                    
                    kubeNodes = kube.info().nodes
                    hostIP = random.choice(kubeNodes).name
                    
                    while 'nodePort' not in s_info['port_forwarding'][0]:
                        log.info('Waiting for service get started before proxifying...')
                        s_info = kube.inspect_service(srv.dns_name)
                        time.sleep(0.5)

                    ip = hostIP
                    p = s_info['port_forwarding'][0]['nodePort']
                    exposedPort = s_info['port_forwarding'][0]['port']
                    base_path = '/zoe/' + uid + '/' + str(id) + '/' + srv.name + '/' + str(exposedPort)
                    original_path = str(ip) + ':' + str(p) + base_path

                    if ip is not None and p is not None:
                        log.info('Proxifying %s', srv.name + ' port ' + str(exposedPort))
                        self.dispatch_to_docker(base_path, original_path)

        except Exception as ex:
            log.error(ex)

    #The apache2 server is running inside a container
    #Adding new entries with the proxy path and the ip:port of the application to the apache2 config file
    def dispatch_to_docker(self, base_path, original_path):
        proxy = ['ProxyPass ' + base_path + '/api/kernels/ ws://' + original_path + '/api/kernels/',
                 'ProxyPassReverse ' + base_path + '/api/kernels/ ws://' + original_path + '/api/kernels/',
                 'ProxyPass ' + base_path + '/terminals/websocket/ ws://' + original_path + '/terminals/websocket/',
                 'ProxyPassReverse ' + base_path + '/terminals/websocket/ ws://' + original_path + '/terminals/websocket/',
                 'ProxyPass ' + base_path + ' http://' + original_path,
                 'ProxyPassReverse ' + base_path + ' http://' + original_path,
                 '',
                 '</VirtualHost>']

        docker_client = docker.Client(base_url=get_conf().proxy_docker_sock)

        delCommand = "sed -i '$ d' " + get_conf().proxy_config_file # /etc/apache2/sites-available/all.conf"
        delID = docker_client.exec_create(get_conf().proxy_container, delCommand)
        docker_client.exec_start(delID)

        for s in proxy:
            command = 'bash -c "echo ' + "'" + s + "'" + '  >> /etc/apache2/sites-available/all.conf"'
            id = docker_client.exec_create(get_conf().proxy_container, command)
            docker_client.exec_start(id)

        reloadCommand = 'service apache2 reload'
        reloadID = docker_client.exec_create(get_conf().proxy_container, reloadCommand)
        docker_client.exec_start(reloadID)

    #Simply remove the added entries at the apache2 config file when terminating applcations
    def unproxify(self, uid, role, id):
        log.info('Unproxifying for user %s - execution %s', uid, str(id))
        pattern = '/zoe\/' + uid + '\/' + str(id) + '/d'
        docker_client = docker.Client(base_url=get_conf().proxy_docker_sock)
        delCommand = 'sed -i "' + pattern + '" ' + get_conf().proxy_config_file #  /etc/apache2/sites-available/all.conf'
        delID = docker_client.exec_create(get_conf().proxy_container, delCommand)
        docker_client.exec_start(delID)
