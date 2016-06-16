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

import json

from flask import render_template, request, redirect, url_for

from zoe_web.web.utils import get_auth, catch_exceptions
import zoe_web.config as config
import zoe_web.api_endpoint
import zoe_web.exceptions


@catch_exceptions
def execution_define():
    get_auth(request)

    return render_template('execution_new.html')


@catch_exceptions
def execution_start():
    uid, role = get_auth(request)
    assert isinstance(config.api_endpoint, zoe_web.api_endpoint.APIEndpoint)

    app_descr_json = request.files['file'].read().decode('utf-8')
    app_descr = json.loads(app_descr_json)
    exec_name = request.form['exec_name']

    new_id = config.api_endpoint.execution_start(uid, role, exec_name, app_descr)

    return redirect(url_for('web.execution_inspect', execution_id=new_id))


@catch_exceptions
def execution_restart(execution_id):
    uid, role = get_auth(request)
    assert isinstance(config.api_endpoint, zoe_web.api_endpoint.APIEndpoint)

    e = config.api_endpoint.execution_by_id(uid, role, execution_id)
    new_id = config.api_endpoint.execution_start(uid, role, e.name, e.description)

    return redirect(url_for('web.execution_inspect', execution_id=new_id))


@catch_exceptions
def execution_terminate(execution_id):
    uid, role = get_auth(request)
    assert isinstance(config.api_endpoint, zoe_web.api_endpoint.APIEndpoint)

    success, message = config.api_endpoint.execution_terminate(uid, role, execution_id)
    if not success:
        raise zoe_web.exceptions.ZoeException(message)

    return redirect(url_for('web.home_user'))


@catch_exceptions
def execution_inspect(execution_id):
    uid, role = get_auth(request)
    assert isinstance(config.api_endpoint, zoe_web.api_endpoint.APIEndpoint)

    e = config.api_endpoint.execution_by_id(uid, role, execution_id)

    services = []
    for sid in e['services']:
        services.append(cont_api.get(sid))

    for s in services:
        s['ip'] = list(s['ip_address'].values())[0]

    template_vars = {
        "e": e,
        "services": services
    }
    return render_template('execution_inspect.html', **template_vars)
