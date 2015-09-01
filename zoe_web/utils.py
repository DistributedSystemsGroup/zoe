from flask import session, redirect, url_for

from zoe_client import ZoeClient


def check_user(zoeclient: ZoeClient):
    if 'user_id' not in session:
        return redirect(url_for('web_bp.index'))
    if not zoeclient.user_check(session['user_id']):
        return redirect(url_for('web_bp.index'))
