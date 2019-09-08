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

"""
This module contains the entrypoint for the commandline Zoe client
"""

from datetime import datetime, timezone
import json
import logging
import os
import sys
import time
from argparse import ArgumentParser, Namespace, FileType, RawDescriptionHelpFormatter
from typing import Tuple

from tabulate import tabulate

from zoe_cmd import utils
from zoe_cmd.api_lib import ZoeAPI
from zoe_lib.exceptions import ZoeAPIException


def _log_stream_stdout(service_id, timestamps, api: ZoeAPI):
    try:
        for line in api.services.get_logs(service_id):
            if timestamps:
                print(line[0], line[1])
            else:
                print(line[1])
    except KeyboardInterrupt:
        print('CTRL-C detected, exiting...')
        return 'interrupt'
    return 'stream_end'


def info_cmd(api: ZoeAPI, args_):
    """Queries the info endpoint."""
    info = api.info.info()
    print("Zoe version: ", info['version'])
    print("Zoe API version: ", info['api_version'])
    print("ZApp format version: ", info['application_format_version'])
    print("Deployment name: ", info['deployment_name'])


def app_get_cmd(api: ZoeAPI, args):
    """Extract an application description from an execution."""
    execution = api.executions.get(args.id)
    if execution is None:
        print("no such execution")
    else:
        json.dump(execution['description'], sys.stdout, sort_keys=True, indent=4)


def exec_list_cmd(api: ZoeAPI, args):
    """List executions"""
    print(api.auth_user)
    filter_names = [
        'status',
        'name',
        'limit',
        'earlier_than_submit',
        'earlier_than_start',
        'earlier_than_end',
        'later_than_submit',
        'later_than_start',
        'later_than_end'
    ]
    filters = {
        'user_id': api.auth_user['id']
    }
    for key, value in vars(args).items():
        if key in filter_names:
            filters[key] = value
    data = api.executions.list(**filters)
    if len(data) == 0:
        return
    tabular_data = [[e['id'], e['name'], e['user_id'], e['status']] for e in sorted(data, key=lambda x: x['id'])]
    headers = ['ID', 'Name', 'User ID', 'Status']
    print(tabulate(tabular_data, headers))


def exec_start_cmd(api: ZoeAPI, args):
    """Submit an execution."""
    app_descr = json.load(args.jsonfile)
    exec_id = api.executions.start(args.name, app_descr)
    if not args.synchronous:
        print("Execution created successfully with ID {}, use the exec-get command to check its status".format(exec_id))
    else:
        print("Execution created successfully with ID {}, waiting for status change".format(exec_id))
        old_status = 'submitted'
        while True:
            execution = api.executions.get(exec_id)
            current_status = execution['status']
            if old_status != current_status:
                print('Execution is now {}'.format(current_status))
                old_status = current_status
            if current_status == 'running':
                break
            time.sleep(0.2)
        if args.running:
            print('Execution running')
            exit(0)
        monitor_service_id = None
        for service_id in execution['services']:
            service = api.services.get(service_id)
            if service['description']['monitor']:
                monitor_service_id = service['id']
                break

        print('\n>------ start of log streaming -------<\n')
        why_stop = _log_stream_stdout(monitor_service_id, False, api)
        print('\n>------ end of log streaming -------<\n')
        if why_stop == 'stream_end':
            print('Execution finished')
            exit(0)
        elif why_stop == 'interrupt':
            print('Do not worry, your execution ({}) is still running.'.format(exec_id))
            exit(1)


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
            service_data = [service['id'], service['name'], 'true' if service['essential'] else 'false', service['status'], service['backend_status'], service['error_message'] if service['error_message'] is not None else '']
            tabular_data.append(service_data)
        headers = ['ID', 'Name', 'Essential', 'Zoe status', 'Backend status', 'Error message']
        print(tabulate(tabular_data, headers))


def exec_kill_cmd(api: ZoeAPI, args):
    """Kill an execution."""
    api.executions.terminate(args.id)
    if args.synchronous:
        while True:
            execution = api.executions.get(exec_id)
            current_status = execution['status']
            if old_status != current_status:
                print('Execution is now {}'.format(current_status))
                old_status = current_status
            if current_status == 'terminated':
                break
            time.sleep(0.2)
        print('Execution terminated')


def logs_cmd(api: ZoeAPI, args):
    """Retrieves and streams the logs of a service."""
    _log_stream_stdout(args.service_id, args.timestamps, api)


def stats_cmd(api: ZoeAPI, args_):
    """Prints statistics on Zoe internals."""
    sched = api.statistics.scheduler()
    print('Scheduler queue length: {}'.format(sched['queue_length']))
    print('Scheduler running queue length: {}'.format(sched['running_length']))
    print('Termination threads count: {}'.format(sched['termination_threads_count']))


ENV_HELP_TEXT = '''To authenticate with Zoe you need to define three environment variables:
ZOE_URL: point to the URL of the Zoe Scheduler (ex.: http://localhost:5000/
ZOE_USER: the username used for authentication
ZOE_PASS: the password used for authentication

or create a ~/.zoerc file (another location can be specified with --api-file) like this:
url = xxx
user = yyy
pass = zzz

Environment variable will override the values specified in the configuration file.
'''


def process_arguments() -> Tuple[ArgumentParser, Namespace]:
    """Parse command line arguments."""
    parser = ArgumentParser(description="Zoe command-line client", epilog=ENV_HELP_TEXT, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--auth-file', type=str, help='Enable debug output', default=os.path.join(os.getenv('HOME', ''), '.zoerc'))

    subparser = parser.add_subparsers()

    # info
    argparser_info = subparser.add_parser('info', help="Queries the API for supported versions")
    argparser_info.set_defaults(func=info_cmd)

    argparser_exec_start = subparser.add_parser('start', help="Start an application")
    argparser_exec_start.add_argument('-s', '--synchronous', action='store_true', help="Do not detach, wait for execution to finish, print main service log")
    argparser_exec_start.add_argument('-r', '--running', action='store_true', help="Do not detach, wait for execution to start (state: running)")
    argparser_exec_start.add_argument('name', help="Name of the execution")
    argparser_exec_start.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_exec_start.set_defaults(func=exec_start_cmd)

    argparser_app_list = subparser.add_parser('exec-ls', help="List all executions for the calling user")
    argparser_app_list.add_argument('--limit', type=int, help='Limit the number of executions')
    argparser_app_list.add_argument('--name', help='Show only executions with this name')
    argparser_app_list.add_argument('--status', choices=["submitted", "queued", "starting", "error", "running", "cleaning up", "terminated"], help='Show only executions with this status')
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

    argparser_app_get = subparser.add_parser('exec-app-get', help="Retrieve an already defined application description")
    argparser_app_get.add_argument('id', help='The ID of the application')
    argparser_app_get.set_defaults(func=app_get_cmd)

    argparser_execution_kill = subparser.add_parser('terminate', help="Terminates an execution")
    argparser_execution_kill.add_argument('id', type=int, help="Execution id")
    argparser_execution_kill.add_argument('-s', '--synchronous', action='store_true', help="Do not detach, wait for execution to terminate")
    argparser_execution_kill.set_defaults(func=exec_kill_cmd)

    argparser_logs = subparser.add_parser('logs', help="Streams the service logs")
    argparser_logs.add_argument('service_id', type=int, help="Service id")
    argparser_logs.add_argument('-t', '--timestamps', action='store_true', help="Prefix timestamps for each line")
    argparser_logs.set_defaults(func=logs_cmd)

    argparser_stats = subparser.add_parser('stats', help="Prints all available statistics")
    argparser_stats.set_defaults(func=stats_cmd)

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
