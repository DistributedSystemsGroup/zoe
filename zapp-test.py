#!/usr/bin/env python3

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

import datetime
import json
import logging
import time

import zoe_lib.applications
from zoe_lib.sql_manager import Execution, Service
from zoe_lib.configargparse import ArgumentParser, FileType

import zoe_master.config as config
from zoe_master.zapp_to_docker import execution_to_containers, terminate_execution
from zoe_master.execution_manager import _digest_application_description

log = logging.getLogger("main")
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(name)s (%(threadName)s): %(message)s'

config_paths = [
    'zoe-master.conf',
    '/etc/zoe/zoe-master.conf'
]


class FakeSQLManager:
    def __init__(self):
        self.executions = []
        self.services = []
        self._last_id = 0

    def execution_list(self, only_one=False, **kwargs):
        ret_list = []
        for e in self.executions:
            for k, v in kwargs.items():
                if getattr(e, k) == v:
                    ret_list.append(e)
        if only_one:
            return ret_list[0]
        else:
            return ret_list

    def execution_update(self, exec_id, **kwargs):
        for e in self.executions:
            if e.id == exec_id:
                for k, v in kwargs.items():
                    if k == "status":
                        continue
                    print(k, v)
                    setattr(e, k, v)
                break

    def execution_new(self, name, user_id, description):
        e_dict = {
            'id': self._last_id,
            'name': name,
            'user_id': user_id,
            'description': description,
            'status': Execution.SUBMIT_STATUS,
            'time_submit': datetime.datetime.now(),
            'time_start': None,
            'time_end': None,
            'error_message': None
        }
        e = Execution(e_dict, self)
        self.executions.append(e)
        self._last_id += 1
        return self._last_id - 1

    def execution_delete(self, execution_id):
        raise NotImplementedError

    def service_list(self, only_one=False, **kwargs):
        ret_list = []
        for e in self.services:
            for k, v in kwargs.items():
                if getattr(e, k) == v:
                    ret_list.append(e)
        if only_one:
            return ret_list[0]
        else:
            return ret_list

    def service_update(self, service_id, **kwargs):
        for e in self.services:
            if e.id == service_id:
                for k, v in kwargs.items():
                    setattr(e, k, v)
                break

    def service_new(self, execution_id, name, service_group, description):
        s_dict = {
            'id': self._last_id,
            'name': name,
            'description': description,
            'status': Execution.SUBMIT_STATUS,
            'execution_id': execution_id,
            'docker_id': None,
            'service_group': service_group,
            'error_message': None
        }
        s = Service(s_dict, self)
        self.services.append(s)
        self._last_id += 1
        return self._last_id - 1


def load_configuration(test_conf=None):
    if test_conf is None:
        argparser = ArgumentParser(description="Zoe application tester - Container Analytics as a Service core component",
                                   default_config_files=config_paths,
                                   auto_env_var_prefix="ZOE_MASTER_",
                                   args_for_setting_config_path=["--config"],
                                   args_for_writing_out_config_file=["--write-config"])
        argparser.add_argument('--debug', action='store_true', help='Enable debug output')
        argparser.add_argument('--swarm', help='Swarm/Docker API endpoint (ex.: zk://zk1:2181,zk2:2181 or http://swarm:2380)', default='http://localhost:2375')
        argparser.add_argument('--api-listen-uri', help='ZMQ API listen address', default='tcp://*:4850')
        argparser.add_argument('--deployment-name', help='name of this Zoe deployment', default='prod')
        argparser.add_argument('--influxdb-dbname', help='Name of the InfluxDB database to use for storing metrics', default='zoe')
        argparser.add_argument('--influxdb-url', help='URL of the InfluxDB service (ex. http://localhost:8086)', default='http://localhost:8086')
        argparser.add_argument('--influxdb-enable', action="store_true", help='Enable metric output toward influxDB')
        argparser.add_argument('--gelf-address', help='Enable Docker GELF log output to this destination (ex. udp://1.2.3.4:1234)', default='')
        argparser.add_argument('--workspace-base-path', help='Path where user workspaces will be created by Zoe. Must be visible at this path on all Swarm hosts.', default='/mnt/zoe-workspaces')
        argparser.add_argument('--overlay-network-name', help='Name of the Swarm overlay network Zoe should use', default='zoe')

        argparser.add_argument('--dbname', help='DB name', default='zoe')
        argparser.add_argument('--dbuser', help='DB user', default='zoe')
        argparser.add_argument('--dbpass', help='DB password', default='zoe')
        argparser.add_argument('--dbhost', help='DB hostname', default='localhost')
        argparser.add_argument('--dbport', type=int, help='DB port', default=5432)

        argparser.add_argument('jsonfile', type=FileType("r"), help='Application description')

        opts = argparser.parse_args()

        opts.gelf_address = ''  # For debugging we want to easily look at logs with 'docker logs'
        opts.influxdb_enable = False  # don't send metrics for these test runs

        if opts.debug:
            argparser.print_values()

        return opts


def main():
    conf = load_configuration()
    config.load_configuration(conf)
    args = config.get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    logging.getLogger('kazoo').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.INFO)
    logging.getLogger("tornado").setLevel(logging.DEBUG)

    state = FakeSQLManager()
    config.singletons['sql_manager'] = state

    zapp_description = json.load(args.jsonfile)

    print('Validating zapp description...')
    zoe_lib.applications.app_validate(zapp_description)

    exec_id = state.execution_new('test', 'fake_user', zapp_description)
    e = state.execution_list(only_one=True, id=exec_id)
    _digest_application_description(e)

    print('Zapp digested, starting containers...')
    execution_to_containers(e)

    for service in e.services:
        print("Service {}, docker ID: {}".format(service.name, service.docker_id))

    print("Execution as been started, press CTRL-C to terminate it")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print('Terminating...')
    terminate_execution(e)

if __name__ == '__main__':
    main()
