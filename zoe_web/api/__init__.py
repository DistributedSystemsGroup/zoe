from io import BytesIO
from zipfile import is_zipfile

from flask import Blueprint, jsonify, request, session, abort, send_file

from zoe_client import ZoeClient
from common.configuration import ipcconf

api_bp = Blueprint('api', __name__)


def _api_check_user(zoe_client):
    if 'user_id' not in session:
        return jsonify(status='error', msg='user not logged in')
    user = zoe_client.user_get(session['user_id'])
    if user is None:
        return jsonify(status='error', msg='unknown user')
    else:
        return user


@api_bp.route('/status/basic')
def status_basic():
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    platform_stats = client.platform_stats()
    ret = {
        'num_nodes': len(platform_stats['swarm']['nodes']),
        'num_containers': platform_stats['swarm']['container_count']
    }
    return jsonify(**ret)


@api_bp.route('/login', methods=['POST'])
def login():
    form_data = request.form
    email = form_data["email"]
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    user = client.user_get_by_email(email)
    if user is None:
        user = client.user_new(email)
    session["user_id"] = user.id
    return jsonify(status="ok")


@api_bp.route('/applications/new', methods=['POST'])
def application_new():
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    user = _api_check_user(client)

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
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    _api_check_user(client)

    if client.application_remove(app_id, False):
        return jsonify(status="error", msg="The application has active executions and cannot be deleted")
    else:
        return jsonify(status="ok")


@api_bp.route('/applications/download/<int:app_id>')
def application_binary_download(app_id: int):
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    _api_check_user(client)

    data = client.application_get_binary(app_id)
    if data is None:
        return jsonify(status="error")
    else:
        return send_file(BytesIO(data), mimetype="application/zip", as_attachment=True, attachment_filename="app-{}.zip".format(app_id))


@api_bp.route('/executions/new', methods=['POST'])
def execution_new():
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    _api_check_user(client)

    form_data = request.form

    app_id = int(form_data["app_id"])
    application = client.application_get(app_id)
    if application.type == "spark-notebook":
        ret = client.execution_spark_new(app_id, form_data["exec_name"])
    else:
        ret = client.execution_spark_new(app_id, form_data["exec_name"], form_data["commandline"], form_data["spark_opts"])

    if ret:
        return jsonify(status="ok")
    else:
        return jsonify(status="error")


@api_bp.route('/executions/logs/container/<int:container_id>')
def execution_logs(container_id: int):
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    _api_check_user(client)

    log = client.log_get(container_id)
    if log is None:
        return jsonify(status="error", msg="no log found")
    else:
        return jsonify(status="ok", log=log)


@api_bp.route('/executions/stats/container/<int:container_id>')
def container_stats(container_id: int):
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    _api_check_user(client)

    stats = client.container_stats(container_id)
    if stats is None:
        return jsonify(status="error", msg="no stats found")
    else:
        return jsonify(status="ok", **stats)


@api_bp.route('/executions/terminate/<int:exec_id>')
def execution_terminate(exec_id: int):
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    _api_check_user(client)

    client.execution_terminate(exec_id)

    return jsonify(status="ok")


@api_bp.route('/history/logs/<int:execution_id>')
def history_logs_get(execution_id: int):
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    _api_check_user(client)

    logs = client.log_history_get(execution_id)
    if logs is None:
        return abort(404)
    else:
        return send_file(BytesIO(logs), mimetype="application/zip", as_attachment=True, attachment_filename="logs-{}.zip".format(execution_id))
