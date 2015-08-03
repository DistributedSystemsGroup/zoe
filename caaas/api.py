from flask import jsonify

from caaas import app
from caaas.swarm import swarm


@app.route("/api/status")
def api_status():
    template_variables = {
        'num_containers': int(swarm.status.num_containers),
        'num_nodes': int(swarm.status.num_nodes)
    }
    return jsonify(**template_variables)
