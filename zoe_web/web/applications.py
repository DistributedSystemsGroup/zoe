from flask import render_template, url_for, redirect, session, abort

import zoe_client.applications as ap
import zoe_client.executions as ex
import zoe_client.users as us

from zoe_web.web import web_bp


@web_bp.route('/apps/new')
def application_new():
    user = us.user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web.index'))

    template_vars = {
        "user_id": user.id,
        "email": user.email,
    }
    return render_template('application_new.html', **template_vars)


@web_bp.route('/app/modify/<app_id>')
def application_modify(app_id):
    return redirect(url_for('web.index'))


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


@web_bp.route('/executions/terminate/<exec_id>')
def execution_terminate(exec_id):
    user = us.user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web.index'))
    execution = ex.execution_get(exec_id)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'execution': execution
    }
    return render_template('execution_terminate.html', **template_vars)


@web_bp.route('/apps/delete/<app_id>')
def application_delete(app_id):
    user = us.user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web.index'))
    application = ap.application_get(app_id)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'app': application
    }
    return render_template('application_delete.html', **template_vars)


@web_bp.route('/executions/inspect/<execution_id>')
def execution_inspect(execution_id):
    user = us.user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web.index'))
    execution = ex.execution_get(execution_id)

    template_vars = {
        "user_id": user.id,
        "email": user.email,
        'execution': execution
    }
    return render_template('execution_inspect.html', **template_vars)
