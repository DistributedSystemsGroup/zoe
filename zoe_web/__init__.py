from flask import Flask, url_for, abort
from zoe_web.api import api_bp
from zoe_web.web import web_bp

app = Flask(__name__, static_url_path='/does-not-exist')
app.register_blueprint(web_bp, url_prefix='')
app.register_blueprint(api_bp, url_prefix='/api')

app.secret_key = b"\xc3\xb0\xa7\xff\x8fH'\xf7m\x1c\xa2\x92F\x1d\xdcz\x05\xe6CJN5\x83!"


def debug_list_routes():
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = "{:50s} {:20s} {}".format(rule.endpoint, methods, url)
        output.append(line)

    for line in sorted(output):
        print(line)


@app.errorhandler(404)
def page_not_found(_):
    debug_list_routes()
