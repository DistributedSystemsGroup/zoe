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

import re
from random import randint

from flask import render_template, redirect, url_for, request, flash
from zoe_lib.applications import ZoeApplicationAPI
from zoe_lib.containers import ZoeContainerAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.predefined_apps.lab_spark import spark_jupyter_notebook_lab_app
from zoe_lib.query import ZoeQueryAPI
from zoe_lib.exceptions import ZoeAPIException

from zoe_web.config import get_conf
from zoe_web.web import web_bp
from zoe_web.web.forms import LoginWithGuestIDForm

guest_id_pattern = re.compile('^\w+$')


@web_bp.route('/', methods=['GET', 'POST'])
def index():
    form = LoginWithGuestIDForm(request.form)
    if request.method == 'POST' and form.validate():
        flash('Valid identifier')
        return redirect(url_for('web.home_guest', guest_identifier=form.guest_identifier.data))
    return render_template('index.html', form=form)


@web_bp.route('/guest/<guest_identifier>')
def home_guest(guest_identifier):
    match = guest_id_pattern.match(guest_identifier)
    if match is None:
        return redirect(url_for('web.index'))

    query_api = ZoeQueryAPI(get_conf().zoe_url, guest_identifier, guest_identifier)

    template_vars = {
        'refresh': randint(2, 8),
        'user_gateway': 'Please wait...',
        'execution_status': 'Please wait...',
        'execution_urls': [],
        'guest_identifier': guest_identifier
    }

    try:
        user = query_api.query('user', name=guest_identifier)
    except ZoeAPIException:
        return redirect(url_for('web.index'))
    if len(user) == 0:
        return redirect(url_for('web.index'))
    else:
        user = user[0]
        template_vars['user_gateway'] = user['gateway_urls'][0]
        template_vars['gateway_ip'] = user['gateway_urls'][0].split('/')[2].split(':')[0]
        app_api = ZoeApplicationAPI(get_conf().zoe_url, guest_identifier, guest_identifier)
        exec_api = ZoeExecutionsAPI(get_conf().zoe_url, guest_identifier, guest_identifier)
        app = query_api.query('application', name='spark-jupyter-lab')
        if len(app) == 0:
            app_descr = spark_jupyter_notebook_lab_app()
            app_api.create(app_descr)
            return render_template('home_guest.html', **template_vars)
        else:
            app = app[0]
            exec = query_api.query('execution', name='guest-lab-{}'.format(guest_identifier))
            if len(exec) == 0:
                exec_api.execution_start('guest-lab-{}'.format(guest_identifier), app['name'])
                template_vars['execution_status'] = 'submitted'
                return render_template('home_guest.html', **template_vars)
            else:
                exec = exec[0]
                if exec['status'] == 'terminated':
                    app_api.delete(app['id'])
                    return render_template('home_guest.html', **template_vars)
                elif exec['status'] != 'running':
                    template_vars['execution_status'] = exec['status']
                    return render_template('home_guest.html', **template_vars)
                else:
                    template_vars['refresh'] = -1
                    cont_api = ZoeContainerAPI(get_conf().zoe_url, guest_identifier, guest_identifier)
                    template_vars['execution_status'] = exec['status']
                    for c_id in exec['containers']:
                        c = cont_api.get(c_id)
                        ip = list(c['ip_address'].values())[0]  # FIXME how to decide which network is the right one?
                        for p in c['ports']:
                            template_vars['execution_urls'].append(('{}'.format(p['name']), '{}://{}:{}{}'.format(p['protocol'], ip, p['port_number'], p['path'])))
                    return render_template('home_guest.html', **template_vars)
