from flask import Blueprint, abort

api = Blueprint('api', __name__)


@api.route('/status/basic')
def basic_status():
    abort(404)
