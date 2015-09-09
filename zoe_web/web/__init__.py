from flask import Blueprint

web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

import zoe_web.web.start
import zoe_web.web.status
import zoe_web.web.applications
