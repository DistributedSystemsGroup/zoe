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

"""Bypass the Zoe scheduler to run a ZApp and leave the logs inside Docker, used for debugging ZApps."""

import datetime
import json
import logging
import time

import zoe_lib.applications
import zoe_lib.config as config
from zoe_lib.configargparse import ArgumentParser, FileType
from zoe_lib.sql_manager import Execution, Service
from zoe_master.execution_manager import _digest_application_description
from zoe_master.zapp_to_docker import execution_to_containers, terminate_execution

log = logging.getLogger("main")
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(name)s (%(threadName)s): %(message)s'

CONFIG_PATHS = [
    'zoe.conf',
    '/etc/zoe/zoe.conf'
]


class FakeSQLManager:
    """A fake in-memory state class."""
    def __init__(self):
        self.executions = []
        self.services = []
        self._last_id = 0

    def execution_list(self, only_one=False, **kwargs):
        """Execution list."""
        ret_list = []
        for e in self.executions:
            for key, value in kwargs.items():
                if getattr(e, key) == value:
                    ret_list.append(e)
        if only_one:
            return ret_list[0]
        else:
            return ret_list

    def execution_update(self, exec_id, **kwargs):
        """Execution update."""
        for e in self.executions:
            if e.id == exec_id:
                for key, value in kwargs.items():
                    if key == "status":
                        continue
                    print(key, value)
                    setattr(e, key, value)
                break

    def execution_new(self, name, user_id, description):
        """New execution."""
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
        """Delete execution."""
        raise NotImplementedError

    def service_list(self, only_one=False, **kwargs):
        """Service list."""
        ret_list = []
        for e in self.services:
            for key, value in kwargs.items():
                if getattr(e, key) == value:
                    ret_list.append(e)
        if only_one:
            return ret_list[0]
        else:
            return ret_list

    def service_update(self, service_id, **kwargs):
        """Service update."""
        for e in self.services:
            if e.id == service_id:
                for key, value in kwargs.items():
                    setattr(e, key, value)
                break

    def service_new(self, execution_id, name, service_group, description):
        """Service new."""
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
        service = Service(s_dict, self)
        self.services.append(service)
        self._last_id += 1
        return self._last_id - 1


def load_configuration():
    """Load configuration from the command line."""
    argparser = ArgumentParser(description="Zoe application tester - Container Analytics as a Service core component",
                               default_config_files=CONFIG_PATHS,
                               auto_env_var_prefix="ZOE_MASTER_",
                               args_for_setting_config_path=["--config"],
                               args_for_writing_out_config_file=["--write-config"])

    argparser.add_argument('--debug', action='store_true', help='Enable debug output')
    argparser.add_argument('--swarm', help='Swarm/Docker API endpoint (ex.: zk://zk1:2181,zk2:2181 or http://swarm:2380)', default='http://localhost:2375')
    argparser.add_argument('--deployment-name', help='name of this Zoe deployment', default='prod')

    argparser.add_argument('--dbname', help='DB name', default='zoe')
    argparser.add_argument('--dbuser', help='DB user', default='zoe')
    argparser.add_argument('--dbpass', help='DB password', default='')
    argparser.add_argument('--dbhost', help='DB hostname', default='localhost')
    argparser.add_argument('--dbport', type=int, help='DB port', default=5432)

    # Master options
    argparser.add_argument('--api-listen-uri', help='ZMQ API listen address', default='tcp://*:4850')
    argparser.add_argument('--influxdb-dbname', help='Name of the InfluxDB database to use for storing metrics', default='zoe')
    argparser.add_argument('--influxdb-url', help='URL of the InfluxDB service (ex. http://localhost:8086)', default='http://localhost:8086')
    argparser.add_argument('--influxdb-enable', action="store_true", help='Enable metric output toward influxDB')
    argparser.add_argument('--gelf-address', help='Enable Docker GELF log output to this destination (ex. udp://1.2.3.4:1234)', default='')
    argparser.add_argument('--workspace-base-path', help='Path where user workspaces will be created by Zoe. Must be visible at this path on all Swarm hosts.', default='/mnt/zoe-workspaces')
    argparser.add_argument('--overlay-network-name', help='Name of the Swarm overlay network Zoe should use', default='zoe')

    # API options
    argparser.add_argument('--listen-address', type=str, help='Address to listen to for incoming connections', default="0.0.0.0")
    argparser.add_argument('--listen-port', type=int, help='Port to listen to for incoming connections', default=5001)
    argparser.add_argument('--master-url', help='URL of the Zoe master process', default='tcp://127.0.0.1:4850')

    # API auth options
    argparser.add_argument('--auth-type', help='Authentication type (text or ldap)', default='text')

    argparser.add_argument('--auth-file', help='Path to the CSV file containing user,pass,role lines for text authentication', default='zoepass.csv')

    argparser.add_argument('--ldap-server-uri', help='LDAP server to use for authentication', default='ldap://localhost')
    argparser.add_argument('--ldap-base-dn', help='LDAP base DN for users', default='ou=something,dc=any,dc=local')
    argparser.add_argument('--ldap-admin-gid', type=int, help='LDAP group ID for admins', default=5000)
    argparser.add_argument('--ldap-user-gid', type=int, help='LDAP group ID for users', default=5001)
    argparser.add_argument('--ldap-guest-gid', type=int, help='LDAP group ID for guests', default=5002)

    argparser.add_argument('jsonfile', type=FileType("r"), help='Application description')

    opts = argparser.parse_args()

    opts.gelf_address = ''  # For debugging we want to easily look at logs with 'docker logs'
    opts.influxdb_enable = False  # don't send metrics for these test runs

    if opts.debug:
        argparser.print_values()

    return opts


def main():
    """The main entrypoint function."""
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

    zapp_description = json.load(args.jsonfile)

    print('Validating zapp description...')
    zoe_lib.applications.app_validate(zapp_description)

    exec_id = state.execution_new('test', 'fake_user', zapp_description)
    e = state.execution_list(only_one=True, id=exec_id)
    _digest_application_description(state, e)

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
