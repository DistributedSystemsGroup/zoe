from caaas.sql import CAaaState
from caaas.cluster_description import SparkClusterDescription
from caaas.spark_app_execution import application_submitted, setup_volume, AppHistory

from flask import Flask
app = Flask(__name__)

from caaas.swarm_manager import SwarmManager

sm = SwarmManager()
sm.connect()

import caaas.web
import caaas.api

from caaas.cleanup_thread import start_cleanup_thread
