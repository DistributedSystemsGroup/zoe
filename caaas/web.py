from flask import render_template

from caaas import app
from caaas.swarm import swarm


@app.route("/web/<username>")
def web_index(username):
    template_vars = {
        "user": username
    }
    return render_template('index.html', **template_vars)


@app.route("/web/<username>/spark-notebook")
def web_notebook(username):
    pass
