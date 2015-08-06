from flask import jsonify
import time

from caaas import app, sm, CAaaState

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
