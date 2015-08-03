from caaas.sql import init_db
from caaas.swarm import swarm

from flask import Flask
app = Flask(__name__)

import caaas.web
import caaas.api
