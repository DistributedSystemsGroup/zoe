from flask import render_template, redirect, url_for, session

from zoe_web.web import web_bp
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.state.application import ApplicationState
from zoe_client.applications import application_list, application_executions_get
from zoe_client.diagnostics import execution_exposed_url
from zoe_client.users import user_get

from common.zoe_storage_client import check


@web_bp.route('/')
def index():
    return render_template('index.html')


@web_bp.route('/home')
def home():
    user = user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web.index'))
    apps = application_list(user.id)
    binaries = {}
    for a in apps:
        assert isinstance(a, ApplicationState)
        if a.description.requires_binary:
            binaries[a.id] = check(a.id, "apps")

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'apps': apps,
        'binaries': binaries
    }
    active_executions = []
    past_executions = []
    for a in apps:
        executions = application_executions_get(a.id)
        for e in executions:
            assert isinstance(e, Execution)
            if e.status == "running" or e.status == "scheduled" or e.status == "submitted" or e.status == "cleaning up":
                if e.status == "running":
                    active_executions.append((a, e, execution_exposed_url(e)))
                else:
                    active_executions.append((a, e))
            else:
                past_executions.append((a, e))

    past_executions.sort(key=lambda x: x[1].time_finished, reverse=True)

    template_vars['active_executions'] = active_executions
    template_vars['past_executions'] = past_executions
    return render_template('home.html', **template_vars)
