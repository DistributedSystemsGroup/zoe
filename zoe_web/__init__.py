from flask import Flask

from zoe_web.api import api_bp
from zoe_web.web import web_bp
from common.configuration import zoeconf

app = Flask(__name__, static_url_path='/does-not-exist')
app.register_blueprint(web_bp, url_prefix='')
app.register_blueprint(api_bp, url_prefix='/api')

app.secret_key = zoeconf.cookies_secret_key
