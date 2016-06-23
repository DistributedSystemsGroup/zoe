# Copyright (c) 2015, Daniele Venzano
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

from zoe_lib.configargparse import ArgumentParser, Namespace

config_paths = [
    'zoe-master.conf',
    '/etc/zoe/zoe-master.conf'
]

# Singletons
scheduler = None
singletons = {
    'metric': None,
    'stats_manager': None,
    'platform_manager': None,
    'workspace_managers': [],
    'api_manager': None,
    'sql_manager': None
}

_conf = None


def load_configuration(test_conf=None):
    global _conf
    if test_conf is None:
        argparser = ArgumentParser(description="Zoe Master - Container Analytics as a Service core component",
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

        opts = argparser.parse_args()
        if opts.debug:
            argparser.print_values()

        _conf = opts
    else:
        _conf = test_conf


def get_conf() -> Namespace:
    return _conf
