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

import time
import logging
import random

import docker

import zoe_api.proxy.base
import zoe_api.api_endpoint
from zoe_master.backends.swarm.api_client import SwarmClient
from zoe_master.backends.kubernetes.api_client import KubernetesClient
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class ApacheProxy(zoe_api.proxy.base.BaseProxy):
    """Apache proxy class."""
    def __init__(self, api_endpoint):
        self.api_endpoint = api_endpoint

    def proxify(self, uid, role, execution_id):  # pylint: disable=too-many-locals
        """Proxify function."""
        try:
            # Wait until all the services get created and started to be able to get the backend_id
            while self.api_endpoint.execution_by_id(uid, role, execution_id).status != 'running':
                log.info('Waiting for all services get started...')
                time.sleep(1)

            exe = self.api_endpoint.execution_by_id(uid, role, execution_id)
            lth = len(exe.services)

            while lth != 0:
                exe = self.api_endpoint.execution_by_id(uid, role, execution_id)
                lth = len(exe.services)
                for srv in exe.services:
                    if srv.backend_id is None:
                        time.sleep(1)
                    else:
                        lth -= 1

            # Start proxifying by adding entry to use proxypass and proxypassreverse in apache2 config file
            for srv in exe.services:
                ip, port = None, None

                if get_conf().backend == 'OldSwarm':
                    swarm = SwarmClient()
                    s_info = swarm.inspect_container(srv.backend_id)
                    port_list = s_info['ports']

                    for key, val in port_list.items():
                        exposed_port = key.split('/tcp')[0]
                        if val is not None:
                            ip = val[0]
                            port = val[1]

                        base_path = '/zoe/' + uid + '/' + str(execution_id) + '/' + srv.name + '/' + exposed_port
                        original_path = str(ip) + ':' + str(port) + base_path

                        if ip is not None and port is not None:
                            log.info('Proxifying %s', srv.name + ' port ' + exposed_port)
                            self.dispatch_to_docker(base_path, original_path)
                else:
                    kube = KubernetesClient(get_conf())
                    s_info = kube.inspect_service(srv.dns_name)

                    kube_nodes = kube.info().nodes
                    host_ip = random.choice(kube_nodes).name

                    while 'nodePort' not in s_info['port_forwarding'][0]:
                        log.info('Waiting for service get started before proxifying...')
                        s_info = kube.inspect_service(srv.dns_name)
                        time.sleep(0.5)

                    ip = host_ip
                    port = s_info['port_forwarding'][0]['nodePort']
                    exposed_port = s_info['port_forwarding'][0]['port']
                    base_path = '/zoe/' + uid + '/' + str(execution_id) + '/' + srv.name + '/' + str(exposed_port)
                    original_path = str(ip) + ':' + str(port) + base_path

                    if ip is not None and port is not None:
                        log.info('Proxifying %s', srv.name + ' port ' + str(exposed_port))
                        self.dispatch_to_docker(base_path, original_path)

        except Exception as ex:
            log.error(ex)

    def dispatch_to_docker(self, base_path, original_path):
        """
        The apache2 server is running inside a container
        Adding new entries with the proxy path and the ip:port of the application to the apache2 config file
        """
        proxy = ['ProxyPass ' + base_path + '/api/kernels/ ws://' + original_path + '/api/kernels/',
                 'ProxyPassReverse ' + base_path + '/api/kernels/ ws://' + original_path + '/api/kernels/',
                 'ProxyPass ' + base_path + '/terminals/websocket/ ws://' + original_path + '/terminals/websocket/',
                 'ProxyPassReverse ' + base_path + '/terminals/websocket/ ws://' + original_path + '/terminals/websocket/',
                 'ProxyPass ' + base_path + ' http://' + original_path,
                 'ProxyPassReverse ' + base_path + ' http://' + original_path,
                 '',
                 '</VirtualHost>']

        docker_client = docker.DockerClient(base_url=get_conf().proxy_docker_sock)

        del_command = "sed -i '$ d' " + get_conf().proxy_config_file  # /etc/apache2/sites-available/all.conf"
        proxy_container = docker_client.containers.get(get_conf().proxy_container)
        proxy_container.exec_run(del_command)

        for entry in proxy:
            command = 'bash -c "echo ' + "'" + entry + "'" + '  >> /etc/apache2/sites-available/all.conf"'
            proxy_container.exec_run(command)

        reload_command = 'service apache2 reload'
        proxy_container.exec_run(reload_command)

    # Simply remove the added entries at the apache2 config file when terminating applications
    def unproxify(self, uid, role, execution_id):
        """Un-proxify."""
        log.info('Unproxifying for user %s - execution %s', uid, str(execution_id))
        pattern = '/zoe\/' + uid + '\/' + str(execution_id) + '/d'  # pylint: disable=anomalous-backslash-in-string
        docker_client = docker.DockerClient(base_url=get_conf().proxy_docker_sock)
        del_command = 'sed -i "' + pattern + '" ' + get_conf().proxy_config_file  # /etc/apache2/sites-available/all.conf'
        proxy_container = docker_client.containers.get(get_conf().proxy_container)
        proxy_container.exec_run(del_command)
