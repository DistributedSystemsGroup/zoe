from datetime import datetime

from flask import Blueprint

web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

import zoe_web.web.start
import zoe_web.web.status
import zoe_web.web.applications


@web_bp.app_template_filter('format_timestamp')
def _jinja2_filter_datetime(timestamp):
    try:
        dt = datetime.fromtimestamp(timestamp)
    except TypeError:
        return timestamp
    return dt.ctime()
