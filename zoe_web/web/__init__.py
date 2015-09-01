from flask import Blueprint, abort, render_template

from zoe_client import ZoeClient
import zoe_web.web.utils as web_utils

web = Blueprint('web', __name__, template_folder='templates', static_folder='static')


@web.route('/')
def index():
    return render_template('index.html')


@web.route('/home')
def home():
    client = ZoeClient()
    user = web_utils.check_user(client)
    template_vars = {
        "user_id": user.id,
        "email": user.email
    }
    return render_template('home.html', **template_vars)
