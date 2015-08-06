from flask import render_template

from caaas import app, sm, CAaaState


@app.route("/web/")
def index():
    return render_template('index.html')


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
    template_vars = {
        "user": username
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


@app.route("/web/status")
def web_status():
    return render_template('status.html')
