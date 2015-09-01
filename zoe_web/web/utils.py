from flask import session, redirect, url_for

from zoe_client import ZoeClient
from zoe_web.web import web_bp
from common.configuration import conf


def get_zoe_client():
    if conf['client_rpyc_autodiscovery']:
        return ZoeClient()
    else:
        return ZoeClient(conf['client_rpyc_server'], conf['client_rpyc_port'])


def check_user(zoeclient: ZoeClient):
    if 'user_id' not in session:
        return redirect(url_for(web_bp.index))
    if not zoeclient.user_check(session['user_id']):
        return redirect(url_for('index'))
