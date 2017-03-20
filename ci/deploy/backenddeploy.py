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
import os
import time
import yaml
import docker
from docker import Client

from utils.docker_container_parameter import DockerContainerParameter #pylint: disable=import-error, no-name-in-module

class ZoeBackendDeploy():
    """ Class deploy zoe backend """
    def __init__(self, dockerUrl, dockerComposePath):
        self.cli = Client(base_url=dockerUrl)
        self.zoe_api = ''
        self.zoe_master = ''
        self.zoe_opts = []
        self.docker_compose_file = dockerComposePath
        self.type_deploy = 1 if 'prod' in dockerComposePath else 0
        self.parse_docker_compose()
        self.previous_img = ''
        self.zoe_postgres = 'zoe-postgres-test'
        self.postgres_conf = 'postgres'
        self.postgre_ip = ''

    def deploy_postgres(self):
        """ deploy postgres and wait until it is ready """
        opts = DockerContainerParameter()

        opts.set_name(self.zoe_postgres)
        opts.set_hostname(self.zoe_postgres)
        opts.set_image(self.postgres_conf + ':latest')

        host_config = self.cli.create_host_config(network_mode='bridge')

        self.cli.create_container(image=opts.get_image(),
                                  hostname=opts.get_hostname(),
                                  name=opts.get_name(),
                                  tty=True,
                                  host_config=host_config,
                                  environment={'POSTGRES_USER': self.postgres_conf,
                                               'POSTGRES_DB': self.postgres_conf,
                                               'POSTGRES_PASSWORD': self.postgres_conf})

        self.cli.start(self.zoe_postgres)

        self.postgres_ip = self.cli.inspect_container(self.zoe_postgres)['NetworkSettings']['Networks']['bridge']['IPAddress'] #pylint: disable=attribute-defined-outside-init

        res = os.popen('scripts/pg_isready -h ' + self.postgres_ip).read()

        while 'no response' in res:
            time.sleep(1)
            print('Waiting for postgres to get ready')
            res = os.popen('scripts/pg_isready -h ' + self.postgres_ip).read()

        for opts in self.zoe_opts:
            cmd = opts.get_command()
            conn = '--dbhost ' + self.postgres_ip
            opts.set_command(cmd.replace('--dbhost', conn))

    def parse_docker_compose(self):
        """ parse docker-compose to get docker configuration """
        content = ''

        with open(self.docker_compose_file, 'r') as stream:
            content = list(yaml.load(stream)['services'].items())

        for i in range(0, 2):

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

    def create_container(self, opts, image): #pylint: disable=too-many-locals
        """ create container """
        port_binds = {}
        volume_binds = {}
        ports = []
        volumes = []

        opts.set_image(image)

        if len(opts.get_ports()) != 0:
            ports_list = opts.get_ports()[0]

            for prt in ports_list:
                splitted = prt.split(":")
                port_binds[int(splitted[0])] = int(splitted[1])
                ports.append(int(splitted[0]))

        if len(opts.get_volumes()) != 0:
            volumes_list = opts.get_volumes()[0]

            for vol in volumes_list:
                splitted = vol.split(":")
                bind = {'bind' : splitted[1], 'mode': 'rw'}
                volume_binds[splitted[0]] = bind
                volumes.append(splitted[1])

        if opts.get_gelf() != '':
            log_config = docker.utils.LogConfig(type='gelf', config={'gelf-address': opts.get_gelf()})
        else:
            log_config = None


        host_config = self.cli.create_host_config(
            network_mode='bridge',
            port_bindings=port_binds,
            binds=volume_binds,
            log_config=log_config)

        ctn = self.cli.create_container(
            image=opts.get_image(),
            command=opts.get_command(),
            hostname=opts.get_hostname(),
            name=opts.get_name(),
            tty=True,
            ports=ports,
            volumes=volumes,
            host_config=host_config)

        print('Created ' + opts.get_name() + '  container')

        return ctn

    def export_ip(self, ctn_name, to_ctn):
        """ get ip of container and export to host file of other container """
        try:
            ip = self.cli.inspect_container(ctn_name)['NetworkSettings']['Networks']['bridge']['IPAddress']
            host_entry = ip + '\t' + ctn_name
            add_to_host = 'bash -c "echo ' + "'" + host_entry + "'" + ' >> /etc/hosts"'
            identifier = self.cli.exec_create(to_ctn, add_to_host)
            self.cli.exec_start(identifier)
        except Exception as ex:
            print(ex)

    def deploy(self, image):
        """ deploy with docker-compose, if success, return, else, fallback """
        try: #pylint: disable=too-many-nested-blocks
            retcode = 1

            for ctn_name in [self.zoe_api, self.zoe_master, self.zoe_postgres]:
                result = self.cli.containers(all=True, filters={'name': ctn_name})
                print(result)
                if len(result) > 0:
                    for res in result:
                        name = res['Names'][0].split("/")[1]
                        if self.type_deploy == 0:
                            if name == ctn_name:
                                self.cli.remove_container(name, force=True)
                        else:
                            if name == ctn_name:
                                img_id = self.cli.inspect_container(ctn_name)['Image']
                                self.previous_img = self.cli.inspect_image(img_id)['RepoTags'][0]
                            self.cli.remove_container(name, force=True)
                        print('Removed ' + name + ' container')
            
            if self.type_deploy == 0:
                print('Deploying postgres...')
                self.deploy_postgres()

            print('deploying with ' + image)
            for opts in self.zoe_opts:
                self.create_container(opts, image)

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
            self.export_ip(self.zoe_master, self.zoe_api)

        except Exception as ex:
            print(ex)
            retcode = 0

        return retcode

    def fallback(self):
        """ fallback to previous success images """
        return
