from flask import session, redirect, url_for

from zoe_client import ZoeClient


def check_user(zoeclient: ZoeClient):
    if 'user_id' not in session:
        return redirect(url_for('web_bp.index'))
    user = zoeclient.user_get(session['user_id'])
    if user is None:
        return redirect(url_for('web_bp.index'))
    else:
        return user
