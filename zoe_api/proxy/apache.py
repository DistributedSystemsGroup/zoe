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

"""Base authenticator class."""

import docker
import time
import logging

import zoe_api.proxy.base
import zoe_api.api_endpoint
from zoe_master.backends.old_swarm.api_client import SwarmClient
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)

class ApacheProxy(zoe_api.proxy.base.BaseProxy):
    """Apache proxy class."""
    def __init__(self, apiEndpoint, appDescription):
        self.appDesc = appDescription
        self.api_endpoint = apiEndpoint

        if self.appDesc is not None:
            services = self.appDesc['services']
            self.total_ctn = 0
            for srv in services:
                self.total_ctn += srv['total_count']

    def proxify(self, uid, role, id):
        try:
            length_service = 0

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
                 
            for srv in exe.services:
                swarm = SwarmClient(get_conf())
                
                s_info = swarm.inspect_container(srv.backend_id)
                ip, p = None, None
                portList = s_info['ports']

                for s in portList.values():
                    if s != None:
                        ip = s[0]
                        p = s[1]

                base_path = '/zoe/' + uid + '/' + str(id) + '/' + srv.name
                original_path = str(ip) + ':' + str(p) + base_path
                
                if ip is not None and p is not None:
                    log.info('Proxifying %s', srv.name)
                    self.dispatch_to_docker(base_path, original_path)

        except Exception as ex:
            log.error(ex)

    def dispatch_to_docker(self, base_path, original_path):
        proxy = ['ProxyPass ' + base_path + '/api/kernels/ ws://' + original_path + '/api/kernels/',
                 'ProxyPassReverse ' + base_path + '/api/kernels/ ws://' + original_path + '/api/kernels/',
                 'ProxyPass ' + base_path + '/terminals/websocket/ ws://' + original_path + '/terminals/websocket/',
                 'ProxyPassReverse ' + base_path + '/terminals/websocket/ ws://' + original_path + '/terminals/websocket/',
                 'ProxyPass ' + base_path + ' http://' + original_path,
                 'ProxyPassReverse ' + base_path + ' http://' + original_path,
                 '',
                 '</VirtualHost>']

        docker_client = docker.Client(base_url="unix:///var/run/docker.sock")

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

    def unproxify(self, uid, role, id):
        log.info('Unproxifying for user %s - execution %s', uid, str(id))
        pattern = '/zoe\/' + uid + '\/' + str(id) + '/d'
        docker_client = docker.Client(base_url="unix:///var/run/docker.sock")
        delCommand = 'sed -i "' + pattern + '" ' + get_conf().proxy_config_file #  /etc/apache2/sites-available/all.conf'
        delID = docker_client.exec_create(get_conf().proxy_container, delCommand)
        docker_client.exec_start(delID)
