from flask import render_template, redirect, url_for, abort

from caaas import app
from caaas.config_parser import config
from caaas.proxy_manager import get_container_addresses
from caaas.sql import CAaaState
from caaas.swarm_manager import sm


@app.route("/web/")
def index():
    return render_template('index.html')


@app.route("/web/status")
def web_status():
    status = sm.swarm_status()
    return render_template('status.html', **status)


@app.route("/web/login/<email>")
def web_login(email):
    state = CAaaState()
    user_id = state.get_user_id(email)
    if user_id is None:
        user_id = state.new_user(email)
    return redirect(url_for("web_index", user_id=user_id))


@app.route("/web/<user_id>")
def web_index(user_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return redirect(url_for('index'))
    template_vars = {
        "user_id": user_id,
        "email": state.get_user_email(user_id)
    }
    return render_template('home.html', **template_vars)


@app.route("/web/<user_id>/apps")
def web_user_apps(user_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return redirect(url_for('index'))

    apps = state.get_applications(user_id)
    template_vars = {
        "user_id": user_id,
        "apps": apps,
        "has_notebook": state.has_notebook(user_id),
        "notebook_address": sm.get_notebook(user_id),
        "notebook_cluster_id": state.get_notebook(user_id)
    }
    return render_template('apps.html', **template_vars)


@app.route("/web/<user_id>/spark-notebook")
def web_notebook(user_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return redirect(url_for('index'))

    template_vars = {
        "user_id": user_id,
        "notebook_address": sm.get_notebook(user_id),
        "max_age": config.cleanup_notebooks_older_than,
        "wrn_time": int(config.cleanup_notebooks_older_than) - int(config.cleanup_notebooks_warning)
    }
    return render_template('notebook.html', **template_vars)


@app.route("/web/<user_id>/cluster/<cluster_id>/inspect")
def web_inspect(user_id, cluster_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return redirect(url_for('index'))

    cluster = state.get_cluster(cluster_id)
    if cluster["user_id"] != user_id:
        abort(404)
    containers = state.get_containers(cluster_id=cluster_id)
    clist = []
    for cid, cinfo in containers.items():
        plist = get_container_addresses(cid)
        clist.append([cinfo["contents"], plist, cid])
    template_vars = {
        "cluster_name": cluster["name"],
        "containers": clist,
        "user_id": user_id
    }
    return render_template('inspect.html', **template_vars)


@app.route("/web/<user_id>/cluster/<cluster_id>/terminate")
def web_terminate(user_id, cluster_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return redirect(url_for('index'))

    cluster = state.get_cluster(cluster_id)
    if cluster["user_id"] != user_id:
        abort(404)
    template_vars = {
        "cluster_name": cluster["name"],
        "cluster_id": cluster_id,
        "user_id": user_id
    }
    return render_template('terminate.html', **template_vars)


@app.route("/web/<user_id>/container/<container_id>/logs")
def web_logs(user_id, container_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return redirect(url_for('index'))

    cont = state.get_container(container_id)
    if user_id != cont["user_id"]:
        abort(404)

    logs = sm.get_log(container_id)
    if logs is None:
        abort(404)
    else:
        logs = logs.decode("ascii")
        ret = {
            'user_id': user_id,
            'cont_contents': cont['contents'],
            "cont_logs": logs
        }
        return render_template('logs.html', **ret)


@app.route("/web/<user_id>/submit-spark-app")
def web_spark_submit(user_id):
    state = CAaaState()
    if not state.check_user_id(user_id):
        return redirect(url_for('index'))

    template_vars = {
        'user_id': user_id,
    }
    return render_template('submit.html', **template_vars)
