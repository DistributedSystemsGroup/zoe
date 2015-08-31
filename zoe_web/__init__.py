from flask import Flask
app = Flask(__name__)

import zoe_web.web
import zoe_web.api
