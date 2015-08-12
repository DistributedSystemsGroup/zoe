from flask import render_template

from caaas import app, sm, CAaaState
from caaas.proxy_manager import get_container_addresses


@app.route("/web/")
def index():
    return render_template('index.html')


@app.route("/web/status")
def web_status():
    return render_template('status.html')


@app.route("/web/<username>")
def web_index(username):
    state = CAaaState()
    state.get_user_id(username)  # creates the user if it does not exists
    template_vars = {
        "user": username
    }
    return render_template('home.html', **template_vars)


@app.route("/web/<username>/status")
def web_user_status(username):
    db = CAaaState()
    user_id = db.get_user_id(username)
    cluster_list = db.get_clusters(user_id)
    for clid in cluster_list:
        cluster_list[clid]["is_notebook"] = cluster_list[clid]["name"] == "notebook"
        cluster_list[clid]["num_containers"] = db.count_containers(user_id, clid)
    template_vars = {
        "user": username,
        "clusters": cluster_list
    }
    return render_template('user-status.html', **template_vars)


@app.route("/web/<username>/spark-notebook")
def web_notebook(username):
    state = CAaaState()
    user_id = state.get_user_id(username)
    template_vars = {
        "user": username,
        "notebook_address": sm.get_notebook(user_id)
    }
    return render_template('notebook.html', **template_vars)


@app.route("/web/<username>/cluster/<cluster_id>/inspect")
def web_inspect(username, cluster_id):
    state = CAaaState()
    user_id = state.get_user_id(username)
    cluster = state.get_cluster(cluster_id)
    if cluster["user_id"] != user_id:
        return ""  # TODO
    containers = state.get_containers(cluster_id=cluster_id)
    clist = []
    for cid, cinfo in containers.items():
        plist = get_container_addresses(cid)
        clist.append([cinfo["contents"], plist, cid])
    template_vars = {
        "cluster_name": cluster["name"],
        "containers": clist,
        "user": username
    }
    return render_template('inspect.html', **template_vars)


@app.route("/web/<username>/cluster/<cluster_id>/terminate")
def web_terminate(username, cluster_id):
    state = CAaaState()
    user_id = state.get_user_id(username)
    cluster = state.get_cluster(cluster_id)
    if cluster["user_id"] != user_id:
        return ""  # TODO
    template_vars = {
        "cluster_name": cluster["name"],
        "cluster_id": cluster_id,
        "user": username
    }
    return render_template('terminate.html', **template_vars)


@app.route("/web/<username>/container/<container_id>/logs")
def web_logs(username, container_id):
    state = CAaaState()
    user_id = state.get_user_id(username)
    # FIXME: check user_id
    cont = state.get_container(container_id)
    logs = sm.get_log(container_id)
    if logs is None:
        ret = {
            'user': username
        }
    else:
        logs = logs.decode("ascii")
        ret = {
            'user': username,
            'cont_contents': cont['contents'],
            "cont_logs": logs
        }
    return render_template('logs.html', **ret)


@app.route("/web/<username>/submit-spark-app")
def web_spark_submit(username):
    state = CAaaState()
    user_id = state.get_user_id(username)
    # FIXME: check user_id
    template_vars = {
        'user': username
    }
    return render_template('submit.html', **template_vars)
