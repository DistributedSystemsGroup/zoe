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

import re
from random import randint
import json

from flask import render_template, request
from zoe_lib.services import ZoeServiceAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.query import ZoeQueryAPI
from zoe_lib.users import ZoeUserAPI
from zoe_lib.exceptions import ZoeAPIException

from zoe_web.config import get_conf
from zoe_web.web import web_bp
from zoe_web.web.auth import missing_auth

guest_id_pattern = re.compile('^\w+$')


@web_bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@web_bp.route('/guest')
def home_guest():
    auth = request.authorization
    if not auth:
        return missing_auth()

    guest_identifier = auth.username
    guest_password = auth.password

    match = guest_id_pattern.match(guest_identifier)
    if match is None:
        return missing_auth()

    query_api = ZoeQueryAPI(get_conf().master_url, guest_identifier, guest_password)
    user_api = ZoeUserAPI(get_conf().master_url, guest_identifier, guest_password)

    template_vars = {
        'refresh': randint(2, 8),
        'user_gateway': 'Please wait...',
        'execution_status': 'Please wait...',
        'execution_urls': [],
        'guest_identifier': guest_identifier
    }

    try:
        user = user_api.get(guest_identifier)
    except ZoeAPIException:
        return missing_auth()
    if user is None:
        return missing_auth()
    else:
        template_vars['user_gateway'] = user['gateway_urls'][0]
        template_vars['gateway_ip'] = user['gateway_urls'][0].split('/')[2].split(':')[0]
        exec_api = ZoeExecutionsAPI(get_conf().master_url, guest_identifier, guest_password)
        app_descr = json.load(open('contrib/zoeapps/eurecom_aml_lab.json', 'r'))
        execution = query_api.query('execution', name='aml-lab')
        if len(execution) == 0 or execution[0]['status'] == 'terminated' or execution[0]['status'] == 'finished':
            exec_api.execution_start('aml-lab', app_descr)
            template_vars['execution_status'] = 'submitted'
            return render_template('home_guest.html', **template_vars)
        else:
            execution = execution[0]
            if execution['status'] != 'running':
                template_vars['execution_status'] = execution['status']
                return render_template('home_guest.html', **template_vars)
            else:
                template_vars['refresh'] = -1
                cont_api = ZoeServiceAPI(get_conf().master_url, guest_identifier, guest_password)
                template_vars['execution_status'] = execution['status']
                for c_id in execution['services']:
                    c = cont_api.get(c_id)
                    ip = list(c['ip_address'].values())[0]  # FIXME how to decide which network is the right one?
                    for p in c['ports']:
                        template_vars['execution_urls'].append(('{}'.format(p['name']), '{}://{}:{}{}'.format(p['protocol'], ip, p['port_number'], p['path'])))
                return render_template('home_guest.html', **template_vars)


@web_bp.route('/user')
def home_user():
    auth = request.authorization
    if not auth:
        return missing_auth()

    guest_identifier = auth.username
    guest_password = auth.password

    query_api = ZoeQueryAPI(get_conf().master_url, guest_identifier, guest_password)

    try:
        user = query_api.query('user', name=guest_identifier)
    except ZoeAPIException:
        return missing_auth()
    if len(user) == 0:
        return missing_auth()
    user = user[0]

    if user['role'] == 'guest':
        return missing_auth()

    executions = query_api.query('execution')
    template_vars = {
        'executions': executions,
        'is_admin': user['role'] == 'admin'
    }

    return render_template('home_user.html', **template_vars)
