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
    tabular_data = [[e['id'], e['name'], e['user_id'], e['status']] for e in sorted(data.values(), key=lambda x: x['id'])]
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
