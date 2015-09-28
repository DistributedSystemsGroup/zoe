from flask import render_template, redirect, url_for, session

import zoe_client.users as us
import zoe_client.diagnostics as di

from zoe_web.web import web_bp


@web_bp.route('/status/platform')
def status_platform():
    user = us.user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web.index'))
    platform_stats = di.platform_stats()

    template_vars = {
        "user_id": user.id,
        "platform": platform_stats
    }
    return render_template('platform_stats.html', **template_vars)
