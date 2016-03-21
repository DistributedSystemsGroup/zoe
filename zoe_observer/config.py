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

from zoe_lib.info import ZoeInfoAPI

config_paths = [
    'zoe-observer.conf',
    '/etc/zoe/zoe-observer.conf'
]

_conf = None


def load_configuration(test_conf=None):
    global _conf
    if test_conf is None:
        argparser = ArgumentParser(description="Zoe Observer - Container Analytics as a Service Swarm Observer component",
                                   default_config_files=config_paths,
                                   auto_env_var_prefix="ZOE_OBSERVER_",
                                   args_for_setting_config_path=["--config"],
                                   args_for_writing_out_config_file=["--write-config"])
        argparser.add_argument('--debug', action='store_true', help='Enable debug output')
        argparser.add_argument('--swarm', help='Swarm/Docker API endpoint (ex.: zk://zk1:2181,zk2:2181 or http://swarm:2380)', default='http://localhost:2375')
        argparser.add_argument('--master-url', help='URL of the master\'s REST API', default='http://127.0.0.1:4850')
        argparser.add_argument('--zoeadmin-password', help='Password used to login as the master Zoe administrator', default='changeme')
        argparser.add_argument('--spark-activity-timeout', help='Number of seconds of inactivity (no jobs run) before a Spark cluster is terminated', type=int, default=18000)
        argparser.add_argument('--loop-time', help='Time between consecutive check', type=int, default=300)

        opts = argparser.parse_args()
        if opts.debug:
            argparser.print_values()
        _conf = opts

        info_api = ZoeInfoAPI(opts.master_url, 'zoeadmin', opts.zoeadmin_password)
        info = info_api.info()
        opts.deployment_name = info['deployment_name']
        # FIXME: check compatibility for API versions
    else:
        _conf = test_conf


def get_conf() -> Namespace:
    return _conf
