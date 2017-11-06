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

"""Configuration parsing."""

import logging

from zoe_lib.configargparse import ArgumentParser, Namespace

logging.getLogger('kazoo').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('docker').setLevel(logging.INFO)

log = logging.getLogger(__name__)

_CONFIG_PATHS = [
    'zoe.conf',
    '/etc/zoe/zoe.conf'
]

_CONF = None


def get_conf() -> Namespace:
    """Returns the conf singleton."""
    return _CONF


def load_configuration(test_conf=None):
    """Parses command line arguments."""
    global _CONF
    if test_conf is None:
        argparser = ArgumentParser(description="Zoe - Container Analytics as a Service",
                                   default_config_files=_CONFIG_PATHS,
                                   auto_env_var_prefix="ZOE_",
                                   args_for_setting_config_path=["--config"],
                                   args_for_writing_out_config_file=["--write-config"])

        # Common options
        argparser.add_argument('--debug', action='store_true', help='Enable debug output')
        argparser.add_argument('--deployment-name', help='name of this Zoe deployment', default='prod')

        argparser.add_argument('--dbname', help='DB name', default='zoe')
        argparser.add_argument('--dbuser', help='DB user', default='zoe')
        argparser.add_argument('--dbpass', help='DB password', default='')
        argparser.add_argument('--dbhost', help='DB hostname', default='localhost')
        argparser.add_argument('--dbport', type=int, help='DB port', default=5432)

        # Master options
        argparser.add_argument('--api-listen-uri', help='ZMQ API listen address', default='tcp://*:4850')

        argparser.add_argument('--kairosdb-enable', action="store_true", help='Enable metric input from KairosDB')
        argparser.add_argument('--kairosdb-url', help='URL of the KairosDB service (ex. http://localhost:8086)', default='http://localhost:8090')

        argparser.add_argument('--workspace-base-path', help='Base directory where user workspaces will be created. Must be visible at this path on all hosts.', default='/mnt/zoe-workspaces')
        argparser.add_argument('--workspace-deployment-path', help='Path appended to the workspace path to distinguish this deployment. If unspecified is equal to the deployment name.', default='--default--')
        argparser.add_argument('--overlay-network-name', help='Name of the Swarm overlay network Zoe should use', default='zoe')

        # Service logs
        argparser.add_argument('--gelf-address', help='Enable Docker GELF log output to this destination (ex. udp://1.2.3.4:7896)', default='')
        argparser.add_argument('--gelf-listener', type=int, help='Enable the internal GELF log listener on this port, set to 0 to disable', default='7896')
        argparser.add_argument('--service-logs-base-path', help='Path where service logs coming from the GELF listener will be stored', default='/var/lib/zoe/service-logs')

        # API options
        argparser.add_argument('--listen-address', type=str, help='Address to listen to for incoming connections', default="0.0.0.0")
        argparser.add_argument('--listen-port', type=int, help='Port to listen to for incoming connections', default=5001)
        argparser.add_argument('--master-url', help='URL of the Zoe master process', default='tcp://127.0.0.1:4850')
        argparser.add_argument('--cookie-secret', help='secret used to encrypt cookies', default='changeme')

        # API auth options
        argparser.add_argument('--auth-type', help='Authentication type (text, ldap or ldapsasl)', default='text')

        argparser.add_argument('--auth-file', help='Path to the CSV file containing user,pass,role lines for text authentication', default='zoepass.csv')

        argparser.add_argument('--ldap-server-uri', help='LDAP server to use for authentication', default='ldap://localhost')
        argparser.add_argument('--ldap-base-dn', help='LDAP base DN for users', default='ou=something,dc=any,dc=local')
        argparser.add_argument('--ldap-admin-gid', type=int, help='LDAP group ID for admins', default=5000)
        argparser.add_argument('--ldap-user-gid', type=int, help='LDAP group ID for users', default=5001)
        argparser.add_argument('--ldap-guest-gid', type=int, help='LDAP group ID for guests', default=5002)

        # Proxy options
        argparser.add_argument('--proxy-path', help='Proxy base path', default='127.0.0.1')

        # Scheduler
        argparser.add_argument('--scheduler-class', help='Scheduler class to use for scheduling ZApps', choices=['ZoeSimpleScheduler', 'ZoeElasticScheduler'], default='ZoeSimpleScheduler')
        argparser.add_argument('--scheduler-policy', help='Scheduler policy to use for scheduling ZApps', choices=['FIFO', 'SIZE'], default='FIFO')

        argparser.add_argument('--backend', choices=['Swarm', 'Kubernetes', 'DockerEngine'], default='Swarm', help='Which backend to enable')
        argparser.add_argument('--backend-image-management', action='store_true', help='Enable image management (not implemented for all backends, check the documentation')

        # Docker Swarm backend options
        argparser.add_argument('--backend-swarm-url', help='Swarm/Docker API endpoint (ex.: zk://zk1:2181,zk2:2181 or http://swarm:2380)', default='http://localhost:2375')
        argparser.add_argument('--backend-swarm-zk-path', help='Swarm/Docker optional ZooKeeper path for Swarm Znodes', default='/docker')
        argparser.add_argument('--backend-swarm-tls-cert', help='Docker TLS certificate file', default='cert.pem')
        argparser.add_argument('--backend-swarm-tls-key', help='Docker TLS private key file', default='key.pem')
        argparser.add_argument('--backend-swarm-tls-ca', help='Docker TLS CA certificate file', default='ca.pem')

        # Docker Engine backend options
        argparser.add_argument('--backend-docker-config-file', help='Location of the Docker Engine config file', default='docker.conf')

        # Kubernetes backend
        argparser.add_argument('--kube-config-file', help='Kubernetes configuration file', default='/opt/zoe/kube.conf')
        argparser.add_argument('--kube-namespace', help='The namespace that Zoe operates on', default='default')

        # other options
        argparser.add_argument('--zapp-shop-path', help='Path where ZApp folders are stored', default='/var/lib/zoe-apps')
        argparser.add_argument('--log-file', help='output logs to a file', default='stderr')
        argparser.add_argument('--max-core-limit', help='Maximum amount of cores users are able to reserve', type=int, default=16)
        argparser.add_argument('--max-memory-limit', help='Maximum amount of memory services can use (in GiB)', type=int, default=64)
        argparser.add_argument('--no-user-edit-limits-web', action='store_true', help='Disable editing ZApp resource limits from the web interface (only admins will able to)')
        argparser.add_argument('--additional-volumes', help='Additional volumes to mount in services filesystems. (ex: /mnt/data:data,/mnt/data_n:data_n)', default='')

        opts = argparser.parse_args()
        if opts.debug:
            argparser.print_values()

        if opts.workspace_deployment_path == '--default--':
            opts.workspace_deployment_path = opts.deployment_name

        if len(opts.additional_volumes) > 0:
            vols = str(opts.additional_volumes).split(',')
            opts.additional_volumes = [v.split(':') for v in vols]
            log.info('Additional volumes:')
            for path, mountpoint in opts.additional_volumes:
                log.info('  - {} -> {}'.format(path, mountpoint))
        else:
            opts.additional_volumes = []

        _CONF = opts
    else:
        _CONF = test_conf
