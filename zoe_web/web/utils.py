from flask import session, redirect, url_for

from zoe_client import ZoeClient
from zoe_web.web import web


def check_user(zoeclient: ZoeClient):
    if 'user_id' not in session:
        return redirect(url_for(web.index))
    if not zoeclient.user_check(session['user_id']):
        return redirect(url_for('index'))
