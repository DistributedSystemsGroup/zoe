from io import BytesIO
import logging
from zipfile import is_zipfile

from flask import Blueprint, jsonify, request, session, abort, send_file

import zoe_client.applications as ap
import zoe_client.diagnostics as di
import zoe_client.executions as ex
import zoe_client.users as us
from zoe_client.predefined_apps.spark import spark_notebook_app, spark_submit_app, spark_ipython_notebook_app
from zoe_client.predefined_apps.hadoop import hdfs_app
import common.zoe_storage_client as storage

api_bp = Blueprint('api', __name__)
log = logging.getLogger(__name__)


def _api_check_user():
    if 'user_id' not in session:
        return jsonify(status='error', msg='user not logged in')
    user = us.user_get(session['user_id'])
    if user is None:
        return jsonify(status='error', msg='unknown user')
    else:
        return user


def _form_field(form: dict, key: str):
    try:
        return form[key]
    except KeyError:
        log.error("the submitted form is missing the {} field".format(key))
        return None


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

    params = {}
    app_name = _form_field(form_data, "app_name")
    if app_name is None:
        return jsonify(status='error', msg='missing app_name in POST')
    fcontents = None
    if form_data['app_type'] == "spark-notebook" or form_data['app_type'] == "spark-submit" or form_data['app_type'] == "ipython-notebook":
        params['name'] = app_name
        keys = ["worker_count", 'master_mem_limit', 'worker_cores', 'worker_mem_limit', 'spark_options', 'master_image', 'worker_image']
        for key in keys:
            v = _form_field(form_data, key)
            if v is None:
                return jsonify(status='error', msg='missing key in POST')
            else:
                params[key] = v
        params['worker_count'] = int(params['worker_count'])
        params['worker_cores'] = int(params['worker_cores'])
        params['master_mem_limit'] = int(params['master_mem_limit']) * 1024 * 1024 * 1024  # 1GiB
        params['worker_mem_limit'] = int(params['worker_mem_limit']) * 1024 * 1024 * 1024  # 1GiB

        if form_data['app_type'] == "spark-notebook":
            notebook_image = _form_field(form_data, 'notebook_image')
            if notebook_image is None:
                return jsonify(status='error', msg='missing notebook_image in POST')
            params['notebook_image'] = notebook_image

            app_descr = spark_notebook_app(**params)
        elif form_data['app_type'] == "spark-submit":
            keys = ['submit_image', 'commandline']
            for key in keys:
                v = _form_field(form_data, key)
                if v is None:
                    return jsonify(status='error', msg='missing key in POST')
                else:
                    params[key] = v

            file_data = request.files['file']
            if not is_zipfile(file_data.stream):
                return jsonify(status='error', msg='not a zip file')
            file_data.stream.seek(0)
            fcontents = file_data.stream.read()

            app_descr = spark_submit_app(**params)
        elif form_data['app_type'] == "ipython-notebook":
            notebook_image = _form_field(form_data, 'ipython_image')
            if notebook_image is None:
                return jsonify(status='error', msg='missing notebook_image in POST')
            params['notebook_image'] = notebook_image
            app_descr = spark_ipython_notebook_app(**params)
        else:
            log.error('Undefined Spark application')
            assert False

    elif form_data['app_type'] == "hadoop-hdfs":
        namenode_image = _form_field(form_data, 'namenode_image')
        datanode_image = _form_field(form_data, 'datanode_image')
        datanode_count = int(_form_field(form_data, 'dn_count'))
        app_descr = hdfs_app(app_name, namenode_image, datanode_count, datanode_image)
    else:
        log.error("unknown application type: {}".format(form_data['app_type']))
        return jsonify(status="error", msg='unknown application type')

    app = ap.application_new(user.id, app_descr)
    if app_descr.requires_binary and fcontents is None:
        log.warn('Creating application without binary file, but the application type needs one')
    elif app_descr.requires_binary and fcontents is not None:
        storage.put(app.id, "apps", fcontents)
    else:
        log.warn('A binary file was provided, but the application does not need one, discarding')

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
