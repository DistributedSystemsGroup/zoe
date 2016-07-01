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

import datetime
import json
import logging
import os
import sys
from argparse import ArgumentParser, Namespace, FileType, RawDescriptionHelpFormatter
from pprint import pprint

from zoe_cmd import utils
from zoe_lib.services import ZoeServiceAPI
from zoe_lib.exceptions import ZoeAPIException, InvalidApplicationDescription
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.applications import app_validate


def app_validate_cmd(args):
    app_descr = json.load(args.jsonfile)
    try:
        app_validate(app_descr)
    except InvalidApplicationDescription as e:
        print(e)
    else:
        print("Static validation OK")


def app_get_cmd(args):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    execution = exec_api.get(args.id)
    if execution is None:
        print("no such execution")
    else:
        json.dump(execution['description'], sys.stdout, sort_keys=True, indent=4)


def exec_list_cmd(_):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = exec_api.list()
    for e in data:
        print('Execution {} (User: {}, ID: {}): {}'.format(e['name'], e['user_id'], e['id'], e['status']))


def exec_start_cmd(args):
    app_descr = json.load(args.jsonfile)
    app_validate(app_descr)
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    ret = exec_api.start(args.name, app_descr)
    print("Application scheduled successfully with ID {}, use the exec-get command to check its status".format(ret))


def exec_get_cmd(args):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    cont_api = ZoeServiceAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    execution = exec_api.get(args.id)
    if execution is None:
        print('Execution not found')
    else:
        print('Execution {} (ID: {})'.format(execution['name'], execution['id']))
        print('Status: {}'.format(execution['status']))
        if execution['status'] == 'error':
            print('Last error: {}'.format(execution['error']))
        print('Time submit: {}'.format(datetime.datetime.fromtimestamp(execution['time_submit'])))

        if execution['time_start'] is None:
            print('Time start: {}'.format('not yet'))
        else:
            print('Time start: {}'.format(datetime.datetime.fromtimestamp(execution['time_start'])))

        if execution['time_end'] is None:
            print('Time end: {}'.format('not yet'))
        else:
            print('Time end: {}'.format(datetime.datetime.fromtimestamp(execution['time_end'])))

        app = execution['description']
        print('Application name: {}'.format(app['name']))
        for c_id in execution['services']:
            c = cont_api.get(c_id)
            ip = list(c['ip_address'].values())[0]  # FIXME how to decide which network is the right one?
            print('Service {} (ID: {})'.format(c['name'], c['id']))
            for p in c['ports']:
                print(' - {}: {}://{}:{}{}'.format(p['name'], p['protocol'], ip, p['port_number'], p['path']))


def exec_kill_cmd(args):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    exec_api.terminate(args.id)


def exec_rm_cmd(args):
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    exec_api.delete(args.id)


ENV_HELP_TEXT = '''To use this tool you need also to define three environment variables:
ZOE_URL: point to the URL of the Zoe Scheduler (ex.: http://localhost:5000/
ZOE_USER: the username used for authentication
ZOE_PASS: the password used for authentication'''


def process_arguments() -> Namespace:
    parser = ArgumentParser(description="Zoe command-line client", epilog=ENV_HELP_TEXT, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    subparser = parser.add_subparsers()

    argparser_app_validate = subparser.add_parser('app-validate', help='Validate an application description')
    argparser_app_validate.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_app_validate.set_defaults(func=app_validate_cmd)

    argparser_exec_start = subparser.add_parser('start', help="Start an application")
    argparser_exec_start.add_argument('name', help="Name of the execution")
    argparser_exec_start.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_exec_start.set_defaults(func=exec_start_cmd)

    argparser_app_list = subparser.add_parser('exec-ls', help="List all executions for the calling user")
    argparser_app_list.set_defaults(func=exec_list_cmd)

    argparser_execution_get = subparser.add_parser('exec-get', help="Get execution status")
    argparser_execution_get.add_argument('id', type=int, help="Execution id")
    argparser_execution_get.set_defaults(func=exec_get_cmd)

    argparser_app_get = subparser.add_parser('exec-app-get', help="Retrieve an already defined application description")
    argparser_app_get.add_argument('id', help='The ID of the application')
    argparser_app_get.set_defaults(func=app_get_cmd)

    argparser_execution_kill = subparser.add_parser('terminate', help="Terminates an execution")
    argparser_execution_kill.add_argument('id', type=int, help="Execution id")
    argparser_execution_kill.set_defaults(func=exec_kill_cmd)

    argparser_execution_kill = subparser.add_parser('exec-rm', help="Deletes an execution")
    argparser_execution_kill.add_argument('id', type=int, help="Execution id")
    argparser_execution_kill.set_defaults(func=exec_rm_cmd)

    return parser, parser.parse_args()


def zoe():
    parser, args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

    if not hasattr(args, "func"):
        parser.print_help()
        return

    if 'ZOE_URL' not in os.environ or 'ZOE_USER' not in os.environ or 'ZOE_PASS' not in os.environ:
        parser.print_help()
        return

    try:
        args.func(args)
    except ZoeAPIException as e:
        print(e.message)
    sys.exit(0)
