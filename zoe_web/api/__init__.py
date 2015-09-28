from io import BytesIO
from zipfile import is_zipfile

from flask import Blueprint, jsonify, request, session, abort, send_file

import zoe_client.applications as ap
import zoe_client.diagnostics as di
import zoe_client.executions as ex
import zoe_client.users as us
import common.zoe_storage_client as storage

api_bp = Blueprint('api', __name__)


def _api_check_user():
    if 'user_id' not in session:
        return jsonify(status='error', msg='user not logged in')
    user = us.user_get(session['user_id'])
    if user is None:
        return jsonify(status='error', msg='unknown user')
    else:
        return user


@api_bp.route('/status/basic')
def status_basic():
    stats = di.platform_stats()
    ret = {
        'num_nodes': len(stats['swarm']['nodes']),
        'num_containers': stats['swarm']['container_count']
    }
    return jsonify(**ret)


@api_bp.route('/login', methods=['POST'])
def login():
    form_data = request.form
    email = form_data["email"]
    user = us.user_get_by_email(email)
    if user is None:
        user = us.user_new(email)
    session["user_id"] = user.id
    return jsonify(status="ok")


@api_bp.route('/applications/new', methods=['POST'])
def application_new():
    user = _api_check_user()

    form_data = request.form

    if form_data['app_type'] == "spark-notebook":
        client.application_spark_notebook_new(user.id, int(form_data["num_workers"]), form_data["ram"] + 'g', int(form_data["num_cores"]), form_data["app_name"])
    elif form_data['app_type'] == "spark-submit":
        file_data = request.files['file']
        if not is_zipfile(file_data.stream):
            return jsonify(status='error', msg='not a zip file')
        file_data.stream.seek(0)
        fcontents = file_data.stream.read()
        client.application_spark_submit_new(user.id, int(form_data["num_workers"]), form_data["ram"] + 'g', int(form_data["num_cores"]), form_data["app_name"], fcontents)
    else:
        return jsonify(status="error", msg='unknown application type')

    return jsonify(status="ok")


@api_bp.route('/applications/delete/<app_id>', methods=['GET', 'POST'])
def application_delete(app_id):
    _api_check_user()

    ap.application_remove(app_id)
    return jsonify(status="ok")


@api_bp.route('/applications/download/<int:app_id>')
def application_binary_download(app_id: int):
    _api_check_user()

    data = ap.application_binary_get(app_id)
    if data is None:
        return jsonify(status="error")
    else:
        return send_file(BytesIO(data), mimetype="application/zip", as_attachment=True, attachment_filename="app-{}.zip".format(app_id))


@api_bp.route('/executions/start/<int:app_id>')
def execution_start(app_id):
    _api_check_user()

    ret = ex.execution_start(app_id)
    if ret:
        return jsonify(status="ok")
    else:
        return jsonify(status="error")


@api_bp.route('/executions/logs/container/<int:container_id>')
def execution_logs(container_id: int):
    _api_check_user()

    log = di.log_get(container_id)
    if log is None:
        return jsonify(status="error", msg="no log found")
    else:
        return jsonify(status="ok", log=log)


@api_bp.route('/executions/stats/container/<int:container_id>')
def container_stats(container_id: int):
    _api_check_user()

    stats = di.container_stats(container_id)
    if stats is None:
        return jsonify(status="error", msg="no stats found")
    else:
        return jsonify(status="ok", **stats)


@api_bp.route('/executions/terminate/<int:exec_id>')
def execution_terminate(exec_id: int):
    _api_check_user()

    ex.execution_kill(exec_id)

    return jsonify(status="ok")


@api_bp.route('/history/logs/<int:execution_id>')
def history_logs_get(execution_id: int):
    _api_check_user()

    logs = storage.get(execution_id, "logs")
    if logs is None:
        return abort(404)
    else:
        return send_file(BytesIO(logs), mimetype="application/zip", as_attachment=True, attachment_filename="logs-{}.zip".format(execution_id))
