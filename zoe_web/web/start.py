from flask import render_template, redirect, url_for

from zoe_client import ZoeClient
from zoe_client.configuration import client_conf
from zoe_web.web import web_bp
import zoe_web.utils as web_utils
from zoe_client.scheduler_classes.execution import Execution


@web_bp.route('/')
def index():
    return render_template('index.html')


@web_bp.route('/home')
def home():
    client = ZoeClient(client_conf().ipc_server, client_conf().ipc_port)
    user = web_utils.check_user(client)
    if user is None:
        return redirect(url_for('web.index'))
    apps = client.application_list(user.id)
    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'apps': apps,
    }
    active_executions = []
    past_executions = []
    for a in apps:
        executions = client.application_executions_get(a.id)
        for e in executions:
            assert isinstance(e, Execution)
            if e.status != "running" or e.status == "scheduled" or e.status == "submitted" or e.status == "cleaning up":
                if e.status == "running":
                    active_executions.append((a, e, "client.execution_get_proxy_path(e.id)"))
                else:
                    active_executions.append((a, e))
            else:
                past_executions.append((a, e))

    past_executions.sort(key=lambda x: x[1].time_finished, reverse=True)

    template_vars['active_executions'] = active_executions
    template_vars['past_executions'] = past_executions
    return render_template('home.html', **template_vars)
