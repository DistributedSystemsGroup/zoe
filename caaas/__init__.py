from caaas.sql import CAaaSSQL

from flask import Flask
app = Flask(__name__)

_db = None


def init_db(user, passw, server, dbname):
    global _db
    _db = CAaaSSQL()
    _db.connect(user, passw, server, dbname)


def get_db():
    """
    :rtype: CAaaSSQL
    """
    return _db

from caaas.swarm import swarm
import caaas.web
import caaas.api
