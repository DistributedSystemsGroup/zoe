from flask import Flask
app = Flask(__name__)

import caaas_web.web
import caaas_web.api
