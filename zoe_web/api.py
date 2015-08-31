from flask import jsonify, request, send_file, abort
import time
from zipfile import is_zipfile

from zoe_web import app
from zoe_web.sql import CAaaState
from zoe_web.spark_app_execution import application_submitted, setup_volume, AppHistory
from zoe_web.swarm_manager import sm

STATS_CACHING_EXPIRATION = 1  # seconds


@app.route("/api/login/<email>")
def api_login(email):
    state = CAaaState()
    user_id = state.get_user_id(email)
    if user_id is None:
        user_id = state.new_user(email)
    return jsonify(user_id=user_id)


@app.route("/api/status")
def api_status():
    if time.time() - sm.last_update_timestamp > STATS_CACHING_EXPIRATION:
        sm.update_status()
    data = {
        'num_containers': int(sm.status.num_containers),
        'num_nodes': int(sm.status.num_nodes)
    }
    return jsonify(**data)


@app.route("/api/<int:user_id>/cluster/<int:cluster_id>/terminate")
def api_terminate_cluster(user_id, cluster_id):
    db = CAaaState()
    ret = {}
    if not db.check_user_id(user_id):
        ret["status"] = "unauthorized"
        return jsonify(**ret)

    cluster_id = str(cluster_id)
    cluster_list = db.get_clusters(user_id)
    if cluster_id not in cluster_list:
        return abort(404)
    if cluster_list[cluster_id]["user_id"] != user_id:
        ret["status"] = "unauthorized"
        return jsonify(**ret)

    if sm.terminate_cluster(cluster_id):
        ret["status"] = "ok"
    else:
        ret["status"] = "error"
    return jsonify(**ret)


@app.route("/api/<int:user_id>/container/<int:container_id>/logs")
def api_container_logs(user_id, container_id):
    db = CAaaState()
    ret = {}
    if not db.check_user_id(user_id):
        ret["status"] = "unauthorized"
        return jsonify(**ret)

    logs = sm.get_log(container_id)
    if logs is None:
        ret["status"] = "no such container"
        ret["logs"] = ''
    else:
        logs = logs.decode("ascii").split("\n")
        ret["status"] = "ok"
        ret["logs"] = logs
    return jsonify(**ret)


@app.route("/api/<int:user_id>/spark-submit", methods=['POST'])
def api_spark_submit(user_id):
    state = CAaaState()
    ret = {}
    if not state.check_user_id(user_id):
        ret["status"] = "unauthorized"
        return jsonify(**ret)

    file_data = request.files['file']
    form_data = request.form
    if not is_zipfile(file_data.stream):
        ret["status"] = "not a zip file"
        return jsonify(**ret)
    app_id = application_submitted(user_id, form_data["exec_name"], form_data["spark_options"], form_data["cmd_line"], file_data)
    setup_volume(user_id, app_id, file_data.stream)
    sm.spark_submit(user_id, app_id)
    ret["status"] = "ok"
    return jsonify(**ret)


@app.route("/api/<int:user_id>/history/<app_id>/logs")
def api_history_log_archive(user_id, app_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return jsonify(status="unauthorized")

    ah = AppHistory(user_id)
    path = ah.get_log_archive_path(app_id)
    return send_file(path, mimetype="application/zip")
