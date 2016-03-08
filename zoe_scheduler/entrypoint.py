#!/usr/bin/python3

# Copyright (c) 2016, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from zoe_scheduler.platform_manager import PlatformManager
from zoe_scheduler.scheduler_policies import FIFOSchedulerPolicy
import zoe_scheduler.config as config
from zoe_scheduler.rest_api import init as api_init
from zoe_scheduler.state.manager import StateManager
from zoe_scheduler.state.blobs.fs import FSBlobs
from zoe_lib.metrics.influxdb import InfluxDBMetricSender
from zoe_scheduler.stats_manager import StatsManager

log = logging.getLogger("main")


def main():
    """
    The entrypoint for the zoe-scheduler script.
    :return: int
    """
    config.load_configuration()
    args = config.get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('kazoo').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.INFO)
    logging.getLogger("tornado").setLevel(logging.DEBUG)
    logging.getLogger('passlib').setLevel(logging.INFO)

    log.info("Initializing state")
    state_manager = StateManager(FSBlobs)
    state_manager.init()

    log.info("Initializing platform manager")
    pm = PlatformManager(FIFOSchedulerPolicy)
    pm.state_manager = state_manager

#    try:
    log.info("Checking state consistency")
    pm.check_state_swarm_consistency()
#    except:
#        log.error('State is seriously corrupted, delete and restart')

    log.info("Initializing API")
    app = api_init(state_manager, pm)

    if config.get_conf().influxdb_enable:
        metrics_th = InfluxDBMetricSender(config.get_conf())
        metrics_th.start()
        config.singletons['metric'] = metrics_th

    stats_th = StatsManager()
    stats_th.start()
    config.singletons['stats_manager'] = stats_th

    log.info("Starting HTTP REST server...")
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(args.listen_port, args.listen_address)  # Initialized like this it is single-threaded/single-process
    ioloop = IOLoop.instance()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        if config.singletons['metric'] is not None:
            config.singletons['metric'].quit()
            config.singletons['metric'].join()
        print("CTRL-C detected, terminating")
