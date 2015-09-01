from flask import Blueprint, abort, jsonify
api_bp = Blueprint('api', __name__)

from zoe_client import get_zoe_client


@api_bp.route('/status/basic')
def status_basic():
    client = get_zoe_client()
    platform_report = client.platform_status()
    ret = {
        'num_nodes': len(platform_report.report["swarm"]["nodes"]),
        'num_containers': platform_report.report["swarm"]["container_count"]
    }
    return jsonify(**ret)
