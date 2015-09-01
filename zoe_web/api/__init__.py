from flask import Blueprint, abort

api_bp = Blueprint('api', __name__)


@api_bp.route('/status/basic')
def basic_status():
    abort(404)
