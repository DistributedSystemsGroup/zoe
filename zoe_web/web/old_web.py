from flask import render_template, redirect, url_for, abort

from zoe_web import app
from zoe_client import ZoeClient


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
