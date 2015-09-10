from flask import render_template

from zoe_client import ZoeClient
from common.configuration import ipcconf
from zoe_web.web import web_bp
import zoe_web.utils as web_utils


@web_bp.route('/status/platform')
def status_platform():
    client = ZoeClient(ipcconf['server'], ipcconf['port'])
    user = web_utils.check_user(client)
    platform_stats = client.platform_stats()

    template_vars = {
        "user_id": user.id,
        "platform": platform_stats
    }
    return render_template('platform_stats.html', **template_vars)
