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

api_endpoint = None  # singleton

config_paths = [
    'zoe-web.conf',
    '/etc/zoe/zoe-web.conf'
]

_conf = None


def load_configuration():
    global _conf
    argparser = ArgumentParser(description="Zoe Web interface: Container Analytics as a Service web component",
                               default_config_files=config_paths,
                               auto_env_var_prefix="ZOE_WEB_",
                               args_for_setting_config_path=["--config"],
                               args_for_writing_out_config_file=["--write-config"])
    argparser.add_argument('--debug', action='store_true', help='Enable debug output')
    argparser.add_argument('--listen-address', type=str, help='Address to listen to for incoming connections', default="0.0.0.0")
    argparser.add_argument('--listen-port', type=int, help='Port to listen to for incoming connections', default=5001)
    argparser.add_argument('--master-url', help='URL of the Zoe master process', default='tcp://127.0.0.1:4850')
    argparser.add_argument('--deployment-name', help='name of this Zoe deployment', default='prod')
    #    argparser.add_argument('--cookie-secret', help='key used to encrypt cookies', default="hr4h3H'kmn F8fz/;CJN5a!")

    argparser.add_argument('--ldap-server-uri', help='LDAP server to use for authentication', default='ldap://localhost')
    argparser.add_argument('--ldap-base-dn', help='LDAP base DN for users', default='ou=something,dc=any,dc=local')
    argparser.add_argument('--ldap-bind-user', help='LDAP user to bind as for user lookup', default='cn=guest,dc=bigfoot,dc=eurecom,dc=fr')
    argparser.add_argument('--ldap-bind-password', help='LDAP user password', default='notsosecret')
    argparser.add_argument('--ldap-admin-gid', type=int, help='LDAP group ID for admins', default=5000)
    argparser.add_argument('--ldap-user-gid', type=int, help='LDAP group ID for users', default=5001)
    argparser.add_argument('--ldap-guest-gid', type=int, help='LDAP group ID for guests', default=5002)

    argparser.add_argument('--dbname', help='DB name', default='zoe')
    argparser.add_argument('--dbuser', help='DB user', default='zoe')
    argparser.add_argument('--dbpass', help='DB password', default='zoe')
    argparser.add_argument('--dbhost', help='DB hostname', default='localhost')
    argparser.add_argument('--dbport', type=int, help='DB port', default=5432)

    opts = argparser.parse_args()
    if opts.debug:
        argparser.print_values()
    _conf = opts


def get_conf() -> Namespace:
    return _conf
