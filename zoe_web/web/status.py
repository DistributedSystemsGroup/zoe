from flask import render_template

from zoe_client import get_zoe_client
from zoe_web.web import web_bp
import zoe_web.utils as web_utils


@web_bp.route('/status/platform')
def status_platform():
    client = get_zoe_client()
    user = web_utils.check_user(client)
    template_vars = {
        "user_id": user.id,
        "email": user.email
    }
    return render_template('status.html', **template_vars)
