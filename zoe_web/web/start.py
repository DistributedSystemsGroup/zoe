from flask import render_template

from zoe_client import get_zoe_client
from zoe_web.web import web_bp
import zoe_web.utils as web_utils


@web_bp.route('/')
def index():
    return render_template('index.html')


@web_bp.route('/home')
def home():
    client = get_zoe_client()
    user = web_utils.check_user(client)
    apps = client.application_list(user.id)
    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'apps': apps,
    }
    reports = [client.application_status(app.id) for app in apps]
    active_executions = []
    past_executions = []
    for r in reports:
        for e in r.report['executions']:
            if e['status'] == "running" or e['status'] == "scheduled" or e['status'] == "submitted":
                active_executions.append((r.report, e, client.execution_get_proxy_path(e['id'])))
            else:
                past_executions.append((r.report, e))
    template_vars['active_executions'] = active_executions
    template_vars['past_executions'] = past_executions
    return render_template('home.html', **template_vars)
