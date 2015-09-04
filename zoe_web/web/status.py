from flask import render_template

from zoe_client import get_zoe_client
from zoe_web.web import web_bp
import zoe_web.utils as web_utils


@web_bp.route('/status/platform')
def status_platform():
    client = get_zoe_client()
    user = web_utils.check_user(client)
    platform_report = client.platform_status().report

    template_vars = {
        "user_id": user.id,
        "platform": platform_report
    }
    return render_template('platform_status.html', **template_vars)
