from flask import render_template, redirect, url_for, abort

from zoe_web import app
from zoe_client import ZoeClient
from common.configuration import conf


@app.route("/web/status")
def web_status():
    client = ZoeClient()
    status = client.platform_status()
    return render_template('status.html', status=status)


@app.route("/web/login/<email>")
def web_login(email):
    client = ZoeClient()
    user_id = client.user_get(email)
    if user_id is None:
        user_id = client.user_new(email)
    return redirect(url_for("web_index", user_id=user_id))


@app.route("/web/<int:user_id>")
def web_index(user_id):
    client = ZoeClient()
    if not client.user_check(user_id):
        return redirect(url_for('index'))
    template_vars = {
        "user_id": user_id,
        "email": client.user_get(user_id).email
    }
    return render_template('home.html', **template_vars)


@app.route("/web/<int:user_id>/apps")
def web_user_apps(user_id):
    client = ZoeClient()
    if not client.user_check(user_id):
        return redirect(url_for('index'))

    apps = client.application_list(user_id)
    template_vars = {
        "user_id": user_id,
        "apps": apps
    }
    return render_template('apps.html', **template_vars)


@app.route("/web/<int:user_id>/spark-notebook")
def web_notebook(user_id):
    client = ZoeClient()
    if not client.user_check(user_id):
        return redirect(url_for('index'))

    template_vars = {
        "user_id": user_id,
        "max_age": conf['notebook_max_age_no_activity'],
        "wrn_time": conf['notebook_max_age_no_activity'] - conf['notebook_warning_age_no_activity']
    }
    return render_template('notebook.html', **template_vars)


@app.route("/web/<int:user_id>/cluster/<int:app_id>/inspect")
def web_inspect(user_id, app_id):
    client = ZoeClient()
    if not client.user_check(user_id):
        return redirect(url_for('index'))

    application = client.application_get(app_id)
    if application.user_id != user_id:
        abort(404)
    app_report = client.application_status(app_id)
    template_vars = {
        "application": app_report,
        "user_id": user_id
    }
    return render_template('inspect.html', **template_vars)


@app.route("/web/<int:user_id>/execution/<int:execution_id>/terminate")
def web_terminate(user_id, execution_id):
    client = ZoeClient()
    if not client.user_check(user_id):
        return redirect(url_for('index'))

    execution = client.execution_get(execution_id)
    application = client.application_get(execution.application_id)
    if application.user_id != user_id:
        abort(404)
    template_vars = {
        "execution_name": execution.name,
        "execution_id": execution_id,
        "user_id": user_id
    }
    return render_template('terminate.html', **template_vars)


@app.route("/web/<int:user_id>/container/<int:container_id>/logs")
def web_logs(user_id, container_id):
    client = ZoeClient()
    if not client.user_check(user_id):
        return redirect(url_for('index'))

    cont = client.container_get(container_id)
    if user_id != cont["user_id"]:
        abort(404)

    logs = client.log_get(container_id)
    if logs is None:
        abort(404)
    else:
        ret = {
            'user_id': user_id,
            'cont_contents': cont['contents'],
            "cont_logs": logs
        }
        return render_template('logs.html', **ret)


@app.route("/web/<int:user_id>/submit-spark-app")
def web_spark_submit(user_id):
    client = ZoeClient()
    if not client.user_check(user_id):
        return redirect(url_for('index'))

    template_vars = {
        'user_id': user_id,
    }
    return render_template('submit.html', **template_vars)
