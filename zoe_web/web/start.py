from flask import render_template

from zoe_client import get_zoe_client
from zoe_web.web import web_bp
import zoe_web.web.utils as web_utils


@web_bp.route('/')
def index():
    return render_template('index.html')


@web_bp.route('/home')
def home():
    client = get_zoe_client()
    user = web_utils.check_user(client)
    template_vars = {
        "user_id": user.id,
        "email": user.email
    }
    return render_template('home.html', **template_vars)
