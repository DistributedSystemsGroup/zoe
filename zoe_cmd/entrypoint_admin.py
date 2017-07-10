# Copyright (c) 2017, Daniele Venzano
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

"""
This module contains the entrypoint for the commandline Zoe client
"""

import json
import logging
import os
import sys
from argparse import ArgumentParser, Namespace, FileType, RawDescriptionHelpFormatter
from typing import Tuple

from tabulate import tabulate

from zoe_cmd import utils
from zoe_lib.info import ZoeInfoAPI
from zoe_lib.exceptions import ZoeAPIException, InvalidApplicationDescription
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.applications import app_validate
from zoe_lib.users import ZoeUsersAPI
from zoe_lib.quota import ZoeQuotaAPI
from zoe_lib.version import ZOE_API_VERSION


def _check_api_version(auth):
    """Checks if there is a version mismatch between server and client."""
    info_api = ZoeInfoAPI(auth['url'], auth['user'], auth['pass'])
    info = info_api.info()
    if info['api_version'] != ZOE_API_VERSION:
        print('Warning: this client understands ZOE API v. {}, but server talks v. {}'.format(ZOE_API_VERSION, info['api_version']))
        print('Warning: certain commands may not work correctly')
        print('Warning: please upgrade or downgrade your client to match the server version')


def app_validate_cmd(auth_, args):
    """Validate an application description."""
    app_descr = json.load(args.jsonfile)
    try:
        app_validate(app_descr)
    except InvalidApplicationDescription as e:
        print(e)
    else:
        print("Static validation OK")


def exec_list_cmd(auth, args):
    """List executions"""
    exec_api = ZoeExecutionsAPI(auth['url'], auth['user'], auth['pass'])
    filter_names = [
        'status',
        'name',
        'user_id',
        'limit',
        'earlier_than_submit',
        'earlier_than_start',
        'earlier_than_end',
        'later_than_submit',
        'later_than_start',
        'later_than_end'
    ]
    filters = {}
    for key, value in vars(args).items():
        if key in filter_names:
            filters[key] = value
    data = exec_api.list(**filters)
    tabular_data = [[e['id'], e['name'], e['user_id'], e['status']] for e in sorted(data.values(), key=lambda x: x['id'])]
    headers = ['ID', 'Name', 'User ID', 'Status']
    print(tabulate(tabular_data, headers))


def user_list_cmd(auth, args_):
    """List users."""
    user_api = ZoeUsersAPI(auth['url'], auth['user'], auth['pass'])
    users = user_api.list()
    data = [[user['id'], user['username'], user['role'], user['email'], user['enabled'], user['priority'], user['quota_id']] for user in sorted(users.values(), key=lambda x: x['username'])]
    headers = ['ID', 'Username', 'Role', 'EMail', 'Enabled', 'Priority', 'Quota ID']
    print(tabulate(data, headers))


def user_enable_cmd(auth, args):
    """Enable a user."""
    user_api = ZoeUsersAPI(auth['url'], auth['user'], auth['pass'])
    user_api.enable(args.username)
    print('User {} enabled'.format(args.username))


def user_disable_cmd(auth, args):
    """Disable a user."""
    user_api = ZoeUsersAPI(auth['url'], auth['user'], auth['pass'])
    user_api.disable(args.username)
    print('User {} disabled'.format(args.username))


def user_email_cmd(auth, args):
    """Set email for a user."""
    user_api = ZoeUsersAPI(auth['url'], auth['user'], auth['pass'])
    user_api.set_email(args.username, args.email)
    print('User {} now has email {}'.format(args.username, args.email))


def user_quota_cmd(auth, args):
    """Set quota for a user."""
    user_api = ZoeUsersAPI(auth['url'], auth['user'], auth['pass'])
    user_api.set_quota(args.username, args.quota_id)
    quota_api = ZoeQuotaAPI(auth['url'], auth['user'], auth['pass'])
    quota = quota_api.get(args.quota_id)
    print('User {} now has quota {}'.format(args.username, quota['name']))


def quota_list_cmd(auth, args_):
    """List quotas"""
    quota_api = ZoeQuotaAPI(auth['url'], auth['user'], auth['pass'])
    quotas = quota_api.list()
    data = [[quota['id'], quota['name'], quota['concurrent_executions'], quota['memory'], quota['cores']] for quota in sorted(quotas.values(), key=lambda x: x['id'])]
    headers = ['ID', 'Name', 'Concurrent executions', 'Memory', 'Cores']
    print(tabulate(data, headers))


def quota_delete_cmd(auth, args):
    """Delete a quota"""
    quota_api = ZoeQuotaAPI(auth['url'], auth['user'], auth['pass'])
    quota = quota_api.get(args.id)
    quota_api.delete(args.id)
    print('Quota {} has been deleted. The default quota has been set for any user with this quota ID.'.format(quota['name']))


def quota_new_cmd(auth, args):
    """Create a new quota."""
    quota_api = ZoeQuotaAPI(auth['url'], auth['user'], auth['pass'])
    new_id = quota_api.new(args.name, args.cc_exec, args.memory, args.cores)
    print('Quota created with ID {}'.format(new_id))


def quota_set_cce_cmd(auth, args):
    """Modify the concurrent executions field for a quota"""
    quota_api = ZoeQuotaAPI(auth['url'], auth['user'], auth['pass'])
    quota_api.set_cc_executions(args.id, args.cc_exec)
    quota = quota_api.get(args.id)
    print('Quota {} concurrent executions set to {}'.format(quota['name'], args.cc_exec))


def quota_set_mem_cmd(auth, args):
    """Modify the concurrent executions field for a quota"""
    quota_api = ZoeQuotaAPI(auth['url'], auth['user'], auth['pass'])
    quota_api.set_memory(args.id, args.memory)
    quota = quota_api.get(args.id)
    print('Quota {} memory set to {}'.format(quota['name'], args.memory))


def quota_set_cores_cmd(auth, args):
    """Modify the concurrent executions field for a quota"""
    quota_api = ZoeQuotaAPI(auth['url'], auth['user'], auth['pass'])
    quota_api.set_cores(args.id, args.cores)
    quota = quota_api.get(args.id)
    print('Quota {} cores set to {}'.format(quota['name'], args.cores))

ENV_HELP_TEXT = '''To authenticate with Zoe you need to define three environment variables:
ZOE_URL: point to the URL of the Zoe Scheduler (ex.: http://localhost:5000/
ZOE_USER: the username used for authentication
ZOE_PASS: the password used for authentication

or create a ~/.zoerc file (another location can be specified with --auth-file) like this:
url = xxx
user = yyy
pass = zzz

Environment variable will override the values specified in the configuration file.
'''


def process_arguments() -> Tuple[ArgumentParser, Namespace]:
    """Parse command line arguments."""
    parser = ArgumentParser(description="Zoe command-line administration client", epilog=ENV_HELP_TEXT, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--auth-file', type=str, help='Enable debug output', default=os.path.join(os.getenv('HOME', ''), '.zoerc'))

    subparser = parser.add_subparsers()

    # users
    parser_aux = subparser.add_parser('user-ls', help='List users known to Zoe')
    parser_aux.set_defaults(func=user_list_cmd)

    parser_aux = subparser.add_parser('user-enable', help='Enable a user')
    parser_aux.add_argument('username', type=str, help='User to enable')
    parser_aux.set_defaults(func=user_enable_cmd)

    parser_aux = subparser.add_parser('user-email', help='Set the email address for a user')
    parser_aux.add_argument('username', type=str, help='User to modify')
    parser_aux.add_argument('email', type=str, help='Email address')
    parser_aux.set_defaults(func=user_email_cmd)

    parser_aux = subparser.add_parser('user-quota', help='Set a new quota for a user')
    parser_aux.add_argument('username', type=str, help='User to modify')
    parser_aux.add_argument('quota_id', type=int, help='Quota ID')
    parser_aux.set_defaults(func=user_quota_cmd)

    # quotas
    parser_aux = subparser.add_parser('quota-ls', help='List defined quotas')
    parser_aux.set_defaults(func=quota_list_cmd)

    parser_aux = subparser.add_parser('quota-delete', help='Delete a quota')
    parser_aux.add_argument('id', type=str, help='Quota ID to delete')
    parser_aux.set_defaults(func=quota_delete_cmd)

    parser_aux = subparser.add_parser('quota-new', help='Create a new quota')
    parser_aux.add_argument('name', type=str, help='New quota name')
    parser_aux.add_argument('cc_exec', type=int, help='Maximum concurrent executions')
    parser_aux.add_argument('memory', type=int, help='Maximum amount of memory the user can reserve')
    parser_aux.add_argument('cores', type=int, help='Maximum amount of cores the user can reserve')
    parser_aux.set_defaults(func=quota_new_cmd)

    parser_aux = subparser.add_parser('quota-set-cce', help='Modify concurrent executions for a quota')
    parser_aux.add_argument('id', type=str, help='Quota ID to modify')
    parser_aux.add_argument('cc_exec', type=int, help='Maximum concurrent executions')
    parser_aux.set_defaults(func=quota_set_cce_cmd)

    parser_aux = subparser.add_parser('quota-set-memory', help='Modify memory for a quota')
    parser_aux.add_argument('id', type=str, help='Quota ID to modify')
    parser_aux.add_argument('memory', type=int, help='Maximum amount of memory the user can reserve')
    parser_aux.set_defaults(func=quota_set_mem_cmd)

    parser_aux = subparser.add_parser('quota-set-cores', help='Modify cores for a quota')
    parser_aux.add_argument('id', type=str, help='Quota ID to modify')
    parser_aux.add_argument('cores', type=int, help='Maximum amount of cores the user can reserve')
    parser_aux.set_defaults(func=quota_set_cores_cmd)

    # zapps
    argparser_zapp_validate = subparser.add_parser('zapp-validate', help='Validate an application description')
    argparser_zapp_validate.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_zapp_validate.set_defaults(func=app_validate_cmd)

    # executions
    argparser_app_list = subparser.add_parser('exec-ls', help="List all executions for the calling user")
    argparser_app_list.add_argument('--limit', type=int, help='Limit the number of executions')
    argparser_app_list.add_argument('--name', help='Show only executions with this name')
    argparser_app_list.add_argument('--user', help='Show only executions belonging to this user')
    argparser_app_list.add_argument('--status', choices=["submitted", "scheduled", "starting", "error", "running", "cleaning up", "terminated"], help='Show only executions with this status')
    argparser_app_list.add_argument('--earlier-than-submit', help='Show only executions submitted earlier than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--earlier-than-start', help='Show only executions started earlier than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--earlier-than-end', help='Show only executions ended earlier than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--later-than-submit', help='Show only executions submitted later than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--later-than-start', help='Show only executions started later than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--later-than-end', help='Show only executions ended later than this timestamp (seconds since UTC epoch)')
    argparser_app_list.set_defaults(func=exec_list_cmd)

    return parser, parser.parse_args()


def zoe():
    """Main entrypoint."""
    parser, args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

    if not hasattr(args, "func"):
        parser.print_help()
        return

    auth = utils.read_auth(args)
    if auth is None:
        sys.exit(1)

    try:
        _check_api_version(auth)
        args.func(auth, args)
    except ZoeAPIException as e:
        print(e.message)
    except KeyboardInterrupt:
        print('CTRL-C pressed, exiting...')
    sys.exit(0)
