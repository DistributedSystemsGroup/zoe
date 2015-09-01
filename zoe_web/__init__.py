from flask import Flask
from zoe_web.api import api
from zoe_web.web import web

app = Flask(__name__)
app.register_blueprint(web, url_prefix='/web')
app.register_blueprint(api, url_prefix='/web/api')

app.secret_key = b"\xc3\xb0\xa7\xff\x8fH'\xf7m\x1c\xa2\x92F\x1d\xdcz\x05\xe6CJN5\x83!"
