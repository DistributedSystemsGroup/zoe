from flask import jsonify, request, send_file
import time
from zipfile import is_zipfile

from caaas import app, sm, CAaaState, application_submitted, setup_volume, AppHistory

STATS_CACHING_EXPIRATION = 1  # seconds


@app.route("/api/status")
def api_status():
    if time.time() - sm.last_update_timestamp > STATS_CACHING_EXPIRATION:
        sm.update_status()
    data = {
        'num_containers': int(sm.status.num_containers),
        'num_nodes': int(sm.status.num_nodes)
    }
    return jsonify(**data)


@app.route("/api/full-status")
def api_full_status():
    db = CAaaState()
    data = {}
    user_list = db.get_all_users()
    for user_id, username in user_list:
        data[username] = {}
        data[username]["num_clusters"] = db.count_clusters(user_id)
        data[username]["num_containers"] = db.count_containers(user_id)
        data[username]["has_notebook"] = db.has_notebook(user_id)
    return jsonify(**data)


@app.route("/api/<username>/status")
def api_user_status(username):
    db = CAaaState()
    user_id = db.get_user_id(username)
    cluster_list = db.get_clusters(user_id)
    for clid in cluster_list:
        cluster_list[clid]["is_notebook"] = cluster_list[clid]["name"] == "notebook"
        cluster_list[clid]["num_containers"] = db.count_containers(user_id, clid)
    return jsonify(**cluster_list)


@app.route("/api/<username>/cluster/<cluster_id>/terminate")
def api_terminate_cluster(username, cluster_id):
    db = CAaaState()
    user_id = db.get_user_id(username)
    cluster_list = db.get_clusters(user_id)
    ret = {}
    if cluster_list[cluster_id]["user_id"] != user_id:
        ret["status"] = "unauthorized"
    else:
        if sm.terminate_cluster(cluster_id):
            ret["status"] = "ok"
        else:
            ret["status"] = "error"
    return jsonify(**ret)


@app.route("/api/<username>/container/<container_id>/logs")
def api_container_logs(username, container_id):
    db = CAaaState()
    user_id = db.get_user_id(username)
    # FIXME: check user_id
    logs = sm.get_log(container_id)
    if logs is None:
        ret = {
            "status": "no such container",
            "logs": ""
        }
    else:
        logs = logs.decode("ascii").split("\n")
        ret = {
            "status": "ok",
            "logs": logs
        }
    return jsonify(**ret)


@app.route("/api/<username>/spark-submit", methods=['POST'])
def api_spark_submit(username):
    file_data = request.files['file']
    form_data = request.form
    state = CAaaState()
    user_id = state.get_user_id(username)
    # FIXME: check user_id
    if not is_zipfile(file_data.stream):
        ret = {
            "status": "not a zip file"
        }
        return jsonify(**ret)
    app_id = application_submitted(user_id, form_data["exec_name"], form_data["spark_options"], form_data["cmd_line"], file_data)
    setup_volume(user_id, app_id, file_data.stream)
    sm.spark_submit(user_id, app_id)
    ret = {
        "status": "ok"
    }
    return jsonify(**ret)


@app.route("/api/<username>/history/<app_id>/logs")
def api_history_log_archive(username, app_id):
    state = CAaaState()
    user_id = state.get_user_id(username)
    # FIXME: check user_id
    ah = AppHistory(user_id)
    path = ah.get_log_archive_path(app_id)
    return send_file(path, mimetype="application/zip")
