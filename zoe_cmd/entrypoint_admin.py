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

from datetime import datetime, timezone
import json
import logging
import os
import sys
from argparse import ArgumentParser, Namespace, FileType, RawDescriptionHelpFormatter
from typing import Tuple

from tabulate import tabulate

from zoe_cmd import utils
from zoe_cmd.api_lib import ZoeAPI
from zoe_lib.exceptions import ZoeAPIException, InvalidApplicationDescription
from zoe_lib.applications import app_validate
from zoe_lib.version import ZOE_API_VERSION


def _check_api_version(api: ZoeAPI):
    """Checks if there is a version mismatch between server and client."""
    info = api.info.info()
    if info['api_version'] != ZOE_API_VERSION:
        print('Warning: this client understands ZOE API v. {}, but server talks v. {}'.format(ZOE_API_VERSION, info['api_version']))
        print('Warning: certain commands may not work correctly')
        print('Warning: please upgrade or downgrade your client to match the server version')


def app_validate_cmd(api_: ZoeAPI, args):
    """Validate an application description."""
    app_descr = json.load(args.jsonfile)
    try:
        app_validate(app_descr)
    except InvalidApplicationDescription as e:
        print(e)
    else:
        print("Static validation OK")


def exec_list_cmd(api: ZoeAPI, args):
    """List executions"""
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
    data = api.executions.list(**filters)
    if len(data) == 0:
        return
    tabular_data = [[e['id'], e['name'], e['user_id'], e['status']] for e in sorted(data, key=lambda x: x['id'])]
    headers = ['ID', 'Name', 'User ID', 'Status']
    print(tabulate(tabular_data, headers))


def exec_get_cmd(api: ZoeAPI, args):
    """Gather information about an execution."""
    execution = api.executions.get(args.id)
    if execution is None:
        print('Execution not found')
    else:
        print('Execution {} (ID: {})'.format(execution['name'], execution['id']))
        print('Application name: {}'.format(execution['description']['name']))
        print('Status: {}'.format(execution['status']))
        if execution['status'] == 'error':
            print('Last error: {}'.format(execution['error_message']))
        print()
        print('Time submit: {}'.format(datetime.fromtimestamp(execution['time_submit'], timezone.utc).astimezone()))

        if execution['time_start'] is None:
            print('Time start: {}'.format('not yet'))
        else:
            print('Time start: {}'.format(datetime.fromtimestamp(execution['time_start'], timezone.utc).astimezone()))

        if execution['time_end'] is None:
            print('Time end: {}'.format('not yet'))
        else:
            print('Time end: {}'.format(datetime.fromtimestamp(execution['time_end'], timezone.utc).astimezone()))
        print()

        endpoints = api.executions.endpoints(execution['id'])
        if endpoints is not None and len(endpoints) > 0:
            print('Exposed endpoints:')
            for endpoint in endpoints:
                print(' - {}: {}'.format(endpoint[0], endpoint[1]))
        else:
            print('This ZApp does not expose any endpoint')

        print()
        tabular_data = []
        for c_id in execution['services']:
            service = api.services.get(c_id)
            service_data = [service['id'], service['name'], 'true' if service['essential'] else 'false', service['status'], service['backend_status'], service['backend_host'], service['error_message'] if service['error_message'] is not None else '']
            tabular_data.append(service_data)
        headers = ['ID', 'Name', 'Essential', 'Zoe status', 'Backend status', 'Host', 'Error message']
        print(tabulate(tabular_data, headers))


def exec_rm_cmd(api: ZoeAPI, args):
    """Delete an execution and kill it if necessary."""
    api.executions.delete(args.id)


def exec_kill_user_cmd(api: ZoeAPI, args):
    """Terminates all executions for the given user."""
    filters = {
        'status': 'running',
        'user_id': args.user_id
    }
    data = api.executions.list(**filters)
    print('Terminating {} executions belonging to user {}'.format(len(data), args.user_id))
    for execution in data:
        api.executions.terminate(execution)
        print('Execution {} terminated'.format(execution))


def quota_ls_cmd(api: ZoeAPI, args):
    """List available quotas."""
    filters = {}
    if 'name' in args:
        filters['name'] = args.name
    quotas = api.quota.list(filters)
    tabular_data = [[q['id'], q['name'], q['concurrent_executions'], q['memory'], q['cores']] for q in sorted(quotas)]
    headers = ['ID', 'Name', 'Conc. Executions', 'Memory', 'Cores']
    print(tabulate(tabular_data, headers))


def quota_get_cmd(api: ZoeAPI, args):
    """Get a quota by its ID."""
    quota = api.quota.get(args.id)
    tabular_data = [[quota['id'], quota['name'], quota['concurrent_executions'], quota['memory'], quota['cores']]]
    headers = ['ID', 'Name', 'Conc. Executions', 'Memory', 'Cores']
    print(tabulate(tabular_data, headers))


def quota_create_cmd(api: ZoeAPI, args):
    """Create a new quota."""
    quota = {
        'name': args.name,
        'concurrent_executions': args.concurrent_executions,
        'memory': args.memory,
        'cores': args.cores
    }
    new_id = api.quota.create(quota)
    print('New quota created with ID: {}'.format(new_id))


def quota_delete_cmd(api: ZoeAPI, args):
    """Delete a quota given its ID."""
    api.quota.delete(args.id)


def quota_update_cmd(api: ZoeAPI, args):
    """Updates an existing quota."""
    quota_update = {}
    if args.name is not None:
        quota_update['name'] = args.name
    if args.concurrent_executions is not None:
        quota_update['concurrent_executions'] = args.concurrent_executions
    if args.memory is not None:
        quota_update['memory'] = args.memory
    if args.cores is not None:
        quota_update['cores'] = args.cores
    api.quota.update(args.id, quota_update)


def role_ls_cmd(api: ZoeAPI, args):
    """List available roles."""
    def b2t(val):
        """Boolean to text."""
        if val:
            return "Yes"
        else:
            return "No"

    filters = {}
    if args.name is not None:
        filters['name'] = args.name
    roles = api.role.list(filters)
    tabular_data = [[r['id'], r['name'], b2t(r['can_see_status']), b2t(r['can_change_config']), b2t(r['can_operate_others']), b2t(r['can_delete_executions']), b2t(r['can_access_api']), b2t(r['can_customize_resources'])] for r in sorted(roles)]
    headers = ['ID', 'Name', 'See status', 'Change config', 'Operate others', 'Delete execs', 'API access', 'Customize resources']
    print(tabulate(tabular_data, headers))


def role_get_cmd(api: ZoeAPI, args):
    """Get a role by its ID."""
    def b2t(val):
        """Boolean to text."""
        if val:
            return "Yes"
        else:
            return "No"

    role = api.role.get(args.id)
    tabular_data = [[role['id'], role['name'], b2t(role['can_see_status']), b2t(role['can_change_config']), b2t(role['can_operate_others']), b2t(role['can_delete_executions']), b2t(role['can_access_api']), b2t(role['can_customize_resources'])]]
    headers = ['ID', 'Name', 'See status', 'Change config', 'Operate others', 'Delete execs', 'API access', 'Customize resources']
    print(tabulate(tabular_data, headers))


def role_create_cmd(api: ZoeAPI, args):
    """Create a new role."""
    role = {
        'name': args.name,
        'can_see_status': True if args.can_see_status else False,
        'can_change_config': True if args.can_change_config else False,
        'can_operate_others': True if args.can_operate_others else False,
        'can_delete_executions': True if args.can_delete_executions else False,
        'can_access_api': True if args.can_access_api else False,
        'can_customize_resources': True if args.can_customize_resources else False,
        'can_access_full_zapp_shop': True if args.can_access_full_zapp_shop else False
    }
    new_id = api.role.create(role)
    print('New role created with ID: {}'.format(new_id))


def role_delete_cmd(api: ZoeAPI, args):
    """Delete a role given its ID."""
    api.role.delete(args.id)


def role_update_cmd(api: ZoeAPI, args):
    """Updates an existing quota."""
    role_update = {}
    if args.name is not None:
        role_update['name'] = args.name
    if args.can_see_status is not None:
        role_update['can_see_status'] = True if args.can_see_status else False
    if args.can_change_config is not None:
        role_update['can_change_config'] = True if args.can_change_config else False
    if args.can_operate_others is not None:
        role_update['can_operate_others'] = True if args.can_operate_others else False
    if args.can_delete_executions is not None:
        role_update['can_delete_executions'] = True if args.can_delete_executions else False
    if args.can_access_api is not None:
        role_update['can_access_api'] = True if args.can_access_api else False
    if args.can_customize_resources is not None:
        role_update['can_customize_resources'] = True if args.can_customize_resources else False
    if args.can_access_full_zapp_shop is not None:
        role_update['can_access_full_zapp_shop'] = True if args.can_access_full_zapp_shop else False
    api.role.update(args.id, role_update)


def user_ls_cmd(api: ZoeAPI, args):
    """List defined users."""
    filters = {}
    if args.username is not None:
        filters['username'] = args.username
    if args.enabled is not None:
        filters['enabled'] = True if args.enabled == 1 else False
    if args.auth_source is not None:
        filters['auth_source'] = args.auth_source
    if args.role is not None:
        role = api.role.list({'name': args.role})[0]
        if role is None:
            print('Unknown role specified')
            return
        filters['role_id'] = role['id']
    if args.quota is not None:
        quota = api.quota.list({'name': args.quota})[0]
        if quota is None:
            print('Unknown quota specified')
            return
        filters['quota_id'] = quota['id']

    users = api.user.list(filters)
    tabular_data = []
    role_cache = {}
    quota_cache = {}
    for user in sorted(users, key=lambda u: u['id']):
        if user['role_id'] in role_cache:
            role = role_cache[user['role_id']]
        else:
            role = api.role.get(user['role_id'])
            role_cache[user['role_id']] = role

        if user['quota_id'] in quota_cache:
            quota = quota_cache[user['quota_id']]
        else:
            quota = api.quota.get(user['quota_id'])
            quota_cache[user['quota_id']] = quota

        tabular_data.append([user['id'], user['username'], user['email'], user['fs_uid'], user['priority'], user['enabled'], user['auth_source'], role['name'], quota['name']])

    headers = ['ID', 'Username', 'Email', 'FS UID', 'Priority', 'Enabled', 'Auth source', 'Role', 'Quota']
    print(tabulate(tabular_data, headers))


def user_get_cmd(api: ZoeAPI, args):
    """Get a user by its ID."""
    user = api.user.get(args.id)
    role = api.role.get(user['role_id'])
    quota = api.quota.get(role['quota_id'])
    tabular_data = [[user['id'], user['username'], user['email'], user['fs_uid'], user['priority'], user['enabled'], user['auth_source'], role['name'], quota['name']]]
    headers = ['ID', 'Username', 'Email', 'FS UID', 'Priority', 'Enabled', 'Auth source', 'Role', 'Quota']
    print(tabulate(tabular_data, headers))


def user_create_cmd(api: ZoeAPI, args):
    """Creates a user."""
    user = {
        'username': args.username,
        'email': args.email,
        'auth_source': args.auth_source,
    }
    quota = api.quota.list({'name': args.quota})[0]
    if quota is None:
        print('Unknown quota')
        return
    user['quota_id'] = quota['id']
    role = api.role.list({'name': args.role})[0]
    if role is None:
        print('Unknown role')
        return
    user['role_id'] = role['id']
    new_id = api.user.create(user)
    print('New user created with ID: {}'.format(new_id))


def user_delete_cmd(api: ZoeAPI, args):
    """Delete a user."""
    api.user.delete(args.id)


def user_update_cmd(api: ZoeAPI, args):
    """Updates a user."""
    user_update = {}
    if args.email is not None:
        user_update['email'] = args.email
    if args.fs_uid is not None:
        user_update['fs_uid'] = args.fs_uid
    if args.password is not None:
        user_update['password'] = args.password
    if args.enabled is not None:
        user_update['enabled'] = args.enabled
    if args.auth_source is not None:
        user_update['auth_source'] = args.auth_source
    if args.priority is not None:
        user_update['priority'] = args.priority
    if args.role_id is not None:
        user_update['role_id'] = args.role_id
    if args.quota_id is not None:
        user_update['quota_id'] = args.quota_id

    api.user.update(args.id, user_update)


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

    # zapps
    argparser_zapp_validate = subparser.add_parser('zapp-validate', help='Validate an application description')
    argparser_zapp_validate.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_zapp_validate.set_defaults(func=app_validate_cmd)

    # executions
    argparser_app_list = subparser.add_parser('exec-ls', help="List all executions for the calling user")
    argparser_app_list.add_argument('--limit', type=int, help='Limit the number of executions')
    argparser_app_list.add_argument('--name', help='Show only executions with this name')
    argparser_app_list.add_argument('--user_id', help='Show only executions belonging to this user')
    argparser_app_list.add_argument('--status', choices=["submitted", "scheduled", "starting", "error", "running", "cleaning up", "terminated"], help='Show only executions with this status')
    argparser_app_list.add_argument('--earlier-than-submit', help='Show only executions submitted earlier than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--earlier-than-start', help='Show only executions started earlier than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--earlier-than-end', help='Show only executions ended earlier than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--later-than-submit', help='Show only executions submitted later than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--later-than-start', help='Show only executions started later than this timestamp (seconds since UTC epoch)')
    argparser_app_list.add_argument('--later-than-end', help='Show only executions ended later than this timestamp (seconds since UTC epoch)')
    argparser_app_list.set_defaults(func=exec_list_cmd)

    argparser_execution_get = subparser.add_parser('exec-get', help="Get execution status")
    argparser_execution_get.add_argument('id', type=int, help="Execution id")
    argparser_execution_get.set_defaults(func=exec_get_cmd)

    argparser_execution_rm = subparser.add_parser('exec-rm', help="Deletes an execution")
    argparser_execution_rm.add_argument('id', type=int, help="Execution id")
    argparser_execution_rm.set_defaults(func=exec_rm_cmd)

    argparser_execution_kill_user = subparser.add_parser('user-terminate', help="Terminate all executions of a user")
    argparser_execution_kill_user.add_argument('user_id', help="User name")
    argparser_execution_kill_user.set_defaults(func=exec_kill_user_cmd)

    # Quotas
    sub_parser = subparser.add_parser('quota-ls', help="List existing quotas")
    sub_parser.add_argument('--name', help="Filter by name")
    sub_parser.set_defaults(func=quota_ls_cmd)

    sub_parser = subparser.add_parser('quota-get', help="Get a quota by its ID")
    sub_parser.add_argument('id', type=int, help="Quota ID")
    sub_parser.set_defaults(func=quota_get_cmd)

    sub_parser = subparser.add_parser('quota-create', help="Create a new quota")
    sub_parser.add_argument('name', help="Quota name")
    sub_parser.add_argument('concurrent_executions', type=int, help="Maximum number of concurrent executions")
    sub_parser.add_argument('memory', type=int, help="Maximum memory in bytes across all running executions")
    sub_parser.add_argument('cores', type=int, help="Maximum number of cores across all running executions")
    sub_parser.set_defaults(func=quota_create_cmd)

    sub_parser = subparser.add_parser('quota-delete', help="Delete a quota")
    sub_parser.add_argument('id', type=int, help="Quota ID")
    sub_parser.set_defaults(func=quota_delete_cmd)

    sub_parser = subparser.add_parser('quota-update', help="Update an existing quota")
    sub_parser.add_argument('id', type=int, help="ID of the quota to update")
    sub_parser.add_argument('--name', help="Quota name")
    sub_parser.add_argument('--concurrent_executions', type=int, help="Maximum number of concurrent executions")
    sub_parser.add_argument('--memory', type=int, help="Maximum memory in bytes across all running executions")
    sub_parser.add_argument('--cores', type=int, help="Maximum number of cores across all running executions")
    sub_parser.set_defaults(func=quota_update_cmd)

    # Roles
    sub_parser = subparser.add_parser('role-ls', help="List existing roles")
    sub_parser.add_argument('--name', help="Filter by name")
    sub_parser.set_defaults(func=role_ls_cmd)

    sub_parser = subparser.add_parser('role-get', help="Get a role by its ID")
    sub_parser.add_argument('id', type=int, help="Role ID")
    sub_parser.set_defaults(func=role_get_cmd)

    sub_parser = subparser.add_parser('role-create', help="Create a new role")
    sub_parser.add_argument('name', help="Role name")
    sub_parser.add_argument('can_see_status', choices=[0, 1], type=int, help="Can access the status web page")
    sub_parser.add_argument('can_change_config', choices=[0, 1], type=int, help="Can change Zoe configuration")
    sub_parser.add_argument('can_operate_others', choices=[0, 1], type=int, help="Can operate on other users' executions")
    sub_parser.add_argument('can_delete_executions', choices=[0, 1], type=int, help="Can delete executions permanently")
    sub_parser.add_argument('can_access_api', choices=[0, 1], type=int, help="Can access the REST API")
    sub_parser.add_argument('can_customize_resources', choices=[0, 1], type=int, help="Can customize resource reservations before starting executions")
    sub_parser.add_argument('can_access_full_zapp_shop', choices=[0, 1], type=int, help="Can access all ZApps in the ZApp shop")
    sub_parser.set_defaults(func=role_create_cmd)

    sub_parser = subparser.add_parser('role-delete', help="Delete a role")
    sub_parser.add_argument('id', type=int, help="Role ID")
    sub_parser.set_defaults(func=role_delete_cmd)

    sub_parser = subparser.add_parser('role-update', help="Update an existing role")
    sub_parser.add_argument('id', type=int, help="ID of the role to update")
    sub_parser.add_argument('--name', help="Role name")
    sub_parser.add_argument('--can_see_status', choices=[0, 1], type=int, help="Can access the status web page")
    sub_parser.add_argument('--can_change_config', choices=[0, 1], type=int, help="Can change Zoe configuration")
    sub_parser.add_argument('--can_operate_others', choices=[0, 1], type=int, help="Can operate on other users' executions")
    sub_parser.add_argument('--can_delete_executions', choices=[0, 1], type=int, help="Can delete executions permanently")
    sub_parser.add_argument('--can_access_api', choices=[0, 1], type=int, help="Can access the REST API")
    sub_parser.add_argument('--can_customize_resources', choices=[0, 1], type=int, help="Can customize resource reservations before starting executions")
    sub_parser.add_argument('--can_access_full_zapp_shop', choices=[0, 1], type=int, help="Can access all ZApps in the ZApp shop")
    sub_parser.set_defaults(func=role_update_cmd)

    # Users
    sub_parser = subparser.add_parser('user-ls', help="List existing users")
    sub_parser.add_argument('--username', help="Filter by user name")
    sub_parser.add_argument('--enabled', type=int, choices=[0, 1], help="Filter by enabled status")
    sub_parser.add_argument('--auth_source', choices=['internal', 'ldap', 'ldap+ssl', 'textfile'], help="Filter by auth source")
    sub_parser.add_argument('--role', help="Filter by role name")
    sub_parser.add_argument('--quota', help="Filter by quota name")
    sub_parser.set_defaults(func=user_ls_cmd)

    sub_parser = subparser.add_parser('user-get', help="Get a user by its ID")
    sub_parser.add_argument('id', type=int, help="User ID")
    sub_parser.set_defaults(func=user_get_cmd)

    sub_parser = subparser.add_parser('user-create', help="Create a new user")
    sub_parser.add_argument('username', help="Username")
    sub_parser.add_argument('email', help="Email")
    sub_parser.add_argument('auth_source', choices=['internal', 'ldap', 'ldap+ssl', 'textfile'], help="Authentication method")
    sub_parser.add_argument('role', help="Role name")
    sub_parser.add_argument('quota', help="Quota name")
    sub_parser.set_defaults(func=user_create_cmd)

    sub_parser = subparser.add_parser('user-delete', help="Delete a user")
    sub_parser.add_argument('id', type=int, help="User ID")
    sub_parser.set_defaults(func=user_delete_cmd)

    sub_parser = subparser.add_parser('user-update', help="Update an existing role")
    sub_parser.add_argument('id', type=int, help="ID of the user to update")
    sub_parser.add_argument('--email', help="Change the email")
    sub_parser.add_argument('--fs_uid', type=int, help="Filesystem UID")
    sub_parser.add_argument('--password', help="Change or set the password for internal authentication")
    sub_parser.add_argument('--enabled', type=int, choices=[0, 1], help="Enable or disable the user")
    sub_parser.add_argument('--auth_source', choices=['internal', 'ldap', 'ldap+ssl', 'textfile'], help="Change the authentication source")
    sub_parser.add_argument('--priority', type=int, help="Change priority")
    sub_parser.add_argument('--role_id', help="Change role")
    sub_parser.add_argument('--quota_id', help="Change quota")
    sub_parser.set_defaults(func=user_update_cmd)

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
        api = ZoeAPI(auth['url'], auth['user'], auth['pass'])
        args.func(api, args)
    except ZoeAPIException as e:
        print(e.message)
    except KeyboardInterrupt:
        print('CTRL-C pressed, exiting...')
    sys.exit(0)
