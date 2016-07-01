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

from flask import render_template, request, g

import zoe_api.api_endpoint
from zoe_api.web.utils import get_auth, catch_exceptions

guest_id_pattern = re.compile('^\w+$')


@catch_exceptions
def index():
    return render_template('index.html')


@catch_exceptions
def home_user():
    uid, role = get_auth(request)
    api_endpoint = g.api_endpoint
    assert isinstance(api_endpoint, zoe_api.api_endpoint.APIEndpoint)

    if role == 'user' or role == 'admin':
        executions = api_endpoint.execution_list(uid, role)

        template_vars = {
            'executions': executions,
            'is_admin': role == 'admin',
        }
        return render_template('home_user.html', **template_vars)
    else:
        template_vars = {
            'refresh': randint(2, 8),
            'execution_status': 'Please wait...',
            'execution_urls': [],
        }

        app_descr = json.load(open('contrib/zoeapps/eurecom_aml_lab.json', 'r'))
        execution = api_endpoint.execution_list(uid, role, name='aml-lab')
        if len(execution) == 0 or execution[0]['status'] == 'terminated' or execution[0]['status'] == 'finished':
            api_endpoint.execution_start(uid, role, 'aml-lab', app_descr)
            template_vars['execution_status'] = 'submitted'
            return render_template('home_guest.html', **template_vars)
        else:
            execution = execution[0]
            if execution['status'] != 'running':
                template_vars['execution_status'] = execution['status']
                return render_template('home_guest.html', **template_vars)
            else:
                template_vars['refresh'] = -1
                template_vars['execution_status'] = execution['status']
                for c_id in execution['services']:
                    c = cont_api.get(c_id)
                    ip = list(c['ip_address'].values())[0]  # FIXME how to decide which network is the right one?
                    for p in c['ports']:
                        template_vars['execution_urls'].append(('{}'.format(p['name']), '{}://{}:{}{}'.format(p['protocol'], ip, p['port_number'], p['path'])))
                return render_template('home_guest.html', **template_vars)
