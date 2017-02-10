#!/usr/bin/env python3

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

"""Backend Deploy."""

import logging
import time
import yaml
from typing import Iterable, Callable, Dict, Any, Union
import docker
from docker import Client

from utils.DockerContainerParameter import DockerContainerParameter

class ZoeBackendDeploy():
    def __init__(self, dockerUrl, dockerComposePath):
        self.cli = Client(base_url=dockerUrl)
        self.zoe_api = ''
        self.zoe_master = ''
        self.zoe_opts = []
        self.docker_compose_file = dockerComposePath
        self.typeDeploy = 1 if 'prod' in dockerComposePath else 0
        self.parse_docker_compose()
        self.previousImage=''

    def parse_docker_compose(self):
        content = ''

        with open(self.docker_compose_file, 'r') as stream:
            content = list(yaml.load(stream)['services'].items())

        for i in range(0,2):

            opts = DockerContainerParameter()

            if 'api' in content[i][0]:
                self.zoe_api = content[i][0]
            else:
                self.zoe_master = content[i][0]

            opts.set_name(content[i][0])

            opts.set_hostname(content[i][0])

            details = content[i][1]

            opts.set_image(details['image'])

            opts.set_command(details['command'])

            if 'volumes' in details:
                opts.set_volumes(details['volumes'])

            if 'ports' in details:
                opts.set_ports(details['ports'])

            if 'logging' in details:
                logging = details['logging']
                if logging['driver'] == 'gelf':
                    opts.set_gelf(logging['options']['gelf-address'])


            self.zoe_opts.append(opts)

    def create_container(self, opts, image):

        port_binds = {}
        volume_binds = {}
        ports = []
        volumes = []

        opts.set_image(image)

        if len(opts.get_ports()) != 0:
            ports_list = opts.get_ports()[0]

            for p in ports_list:
                splitted = p.split(":")
                port_binds[int(splitted[0])] = int(splitted[1])
                ports.append(int(splitted[0]))

        if len(opts.get_volumes()) != 0:
            volumes_list = opts.get_volumes()[0]

            for v in volumes_list:
                splitted = v.split(":")
                bind = {'bind' : splitted[1], 'mode': 'rw'}
                volume_binds[splitted[0]] = bind
                volumes.append(splitted[1])

        if opts.get_gelf() != '':
            log_config = docker.utils.LogConfig(type = 'gelf', config = {'gelf-address': opts.get_gelf()})


        host_config = self.cli.create_host_config(
            network_mode='bridge',
            port_bindings= port_binds,
            binds= volume_binds,
            log_config = log_config)

        ctn = self.cli.create_container(
            image = opts.get_image(),
            command = opts.get_command(),
            hostname = opts.get_hostname(),
            name = opts.get_name(),
            tty=True,
            ports=ports,
            volumes=volumes,
            host_config=host_config)

        print('Created ' + opts.get_name() + '  container')

        return ctn

    def export_master_ip(self):
        try:
            ip_zoe_master = self.cli.inspect_container(self.zoe_master)['NetworkSettings']['Networks']['bridge']['IPAddress']
            hostEntry = ip_zoe_master + '\t' + self.zoe_master
            add_to_host = 'bash -c "echo ' + "'" + hostEntry + "'" + ' >> /etc/hosts"'
            id = self.cli.exec_create(self.zoe_api, add_to_host)
            self.cli.exec_start(id)
        except Exception as ex:
            print(ex)

    def deploy(self, image):
        '''deploy with docker-compose, if success, return, else, fallback '''
        try:

            retcode = 1

            for s in [self.zoe_api, self.zoe_master]:
                res = self.cli.containers(all=True, filters={'name': s})
                if len(res) > 0:
                    for r in res:
                        name = r['Names'][0].split("/")[1]
                        if self.typeDeploy == 0:
                            if name == s:
                                self.cli.remove_container(name, force=True)
                        else:
                            if name == s:
                                imgID = self.cli.inspect_container(s)['Image']
                                self.previousImage = self.cli.inspect_image(imgID)['RepoTags'][0]
                            self.cli.remove_container(name, force=True)
                        print('Removed ' + name + ' container')

            print('deploying with ' + image)
            for opts in self.zoe_opts:
                ctn = self.create_container(opts, image)

            print('Deploying zoe backend...')

            #start zoe_api
            self.cli.start(self.zoe_api)
            print('Started latest ' + self.zoe_api + ' container...')
            if not self.cli.inspect_container(self.zoe_api)['State']['Running']:
                retcode = -1
    
            time.sleep(5)
    
            #start zoe_master
            self.cli.start(self.zoe_master)
            print('Started latest ' + self.zoe_master + ' container...')
            if not self.cli.inspect_container(self.zoe_master)['State']['Running']:
                retcode = 0

            #export zoe-master ip address to hosts file of zoe-api
            self.export_master_ip()

        except Exception as ex:
            print(ex)
            retcode = 0
            pass

        return retcode

    def fallback(self, image):
        return

