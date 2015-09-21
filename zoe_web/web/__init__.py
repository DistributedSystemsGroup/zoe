from flask import Blueprint

web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

import zoe_web.web.start
import zoe_web.web.status
import zoe_web.web.applications

from common.version import __version__


@web_bp.context_processor
def inject_version():
    return dict(zoe_version=__version__)
