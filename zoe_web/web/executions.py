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

from flask import render_template, request, redirect, url_for

from zoe_lib.services import ZoeServiceAPI
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.query import ZoeQueryAPI
from zoe_lib.users import ZoeUserAPI
from zoe_lib.exceptions import ZoeAPIException

from zoe_web.config import get_conf
from zoe_web.web import web_bp
from zoe_web.web.auth import missing_auth


@web_bp.route('/executions/start/<app_id>')
def execution_start(app_id):
    user = us.user_get(session["user_id"])
    if user is None:
        return redirect(url_for('web.index'))
    application = ap.application_get(app_id)
    if application is None:
        return abort(404)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'app': application
    }
    return render_template('execution_new.html', **template_vars)


@web_bp.route('/executions/restart/<int:execution_id>')
def execution_restart(execution_id):
    auth = request.authorization
    if not auth:
        return missing_auth()

    guest_identifier = auth.username
    guest_password = auth.password

    exec_api = ZoeExecutionsAPI(get_conf().master_url, guest_identifier, guest_password)
    e = exec_api.execution_get(execution_id)
    new_id = exec_api.execution_start(e['name'], e['application'])

    return redirect(url_for('web.execution_inspect', execution_id=new_id))


@web_bp.route('/executions/terminate/<int:execution_id>')
def execution_terminate(execution_id):
    auth = request.authorization
    if not auth:
        return missing_auth()

    guest_identifier = auth.username
    guest_password = auth.password

    exec_api = ZoeExecutionsAPI(get_conf().master_url, guest_identifier, guest_password)
    e = exec_api.execution_get(execution_id)
    exec_api.terminate(execution_id)

    return redirect(url_for('web.home_user'))


@web_bp.route('/executions/inspect/<int:execution_id>')
def execution_inspect(execution_id):
    auth = request.authorization
    if not auth:
        return missing_auth()

    guest_identifier = auth.username
    guest_password = auth.password

    exec_api = ZoeExecutionsAPI(get_conf().master_url, guest_identifier, guest_password)
    cont_api = ZoeServiceAPI(get_conf().master_url, guest_identifier, guest_password)

    e = exec_api.execution_get(execution_id)

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
