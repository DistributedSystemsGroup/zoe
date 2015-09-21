from flask import session, redirect, url_for

from zoe_client import ZoeClient


def check_user(zoeclient: ZoeClient):
    if 'user_id' not in session:
        return None
    user = zoeclient.user_get(session['user_id'])
    if user is None:
        return None
    else:
        return user
