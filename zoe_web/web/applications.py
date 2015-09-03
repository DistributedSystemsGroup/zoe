from flask import render_template

from zoe_client import get_zoe_client
from zoe_web.web import web_bp
import zoe_web.utils as web_utils


@web_bp.route('/apps/new')
def application_new():
    client = get_zoe_client()
    user = web_utils.check_user(client)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
    }
    return render_template('application_new.html', **template_vars)


@web_bp.route('/executions/new/<app_id>')
def execution_new(app_id):
    client = get_zoe_client()
    user = web_utils.check_user(client)
    application = client.application_get(app_id)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'app': application
    }
    return render_template('execution_new.html', **template_vars)


@web_bp.route('/executions/terminate/<exec_id>')
def execution_terminate(exec_id):
    client = get_zoe_client()
    user = web_utils.check_user(client)
    execution = client.execution_get(exec_id)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'execution': execution
    }
    return render_template('execution_terminate.html', **template_vars)


@web_bp.route('/apps/delete/<app_id>')
def application_delete(app_id):
    client = get_zoe_client()
    user = web_utils.check_user(client)
    application = client.application_get(app_id)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'app': application
    }
    return render_template('application_delete.html', **template_vars)
