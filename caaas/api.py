from flask import jsonify

from caaas import app, swarm, get_db


@app.route("/api/status")
def api_status():
    data = {
        'num_containers': int(swarm.status.num_containers),
        'num_nodes': int(swarm.status.num_nodes)
    }
    return jsonify(**data)


@app.route("/api/full-status")
def api_full_status():
    db = get_db()
    data = {}
    user_list = db.get_all_users()
    for user_id, username in user_list:
        data[username] = {}
        data[username]["num_clusters"] = db.count_clusters(user_id)
        data[username]["num_containers"] = db.count_containers(user_id)
        data[username]["has_notebook"] = db.has_notebook(user_id)
    return jsonify(**data)
