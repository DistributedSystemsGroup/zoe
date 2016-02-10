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
from zoe_scheduler.config import load_configuration, get_conf
from zoe_scheduler.rest_api import init as api_init
from zoe_scheduler.state.manager import StateManager
from zoe_scheduler.state.blobs.fs import FSBlobs

log = logging.getLogger("main")


def main():
    """
    The entrypoint for the zoe-scheduler script.
    :return: int
    """
    load_configuration()
    args = get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('kazoo').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.INFO)
    logging.getLogger("tornado").setLevel(logging.DEBUG)
    logging.getLogger('passlib').setLevel(logging.INFO)

    state_manager = StateManager(FSBlobs)
    state_manager.init()

    pm = PlatformManager(FIFOSchedulerPolicy)
    pm.state_manager = state_manager

#    try:
    pm.check_state_swarm_consistency()
#    except:
#        log.error('State is seriously corrupted, delete and restart')

    app = api_init(state_manager, pm)

    log.info("Starting HTTP REST server...")
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(args.listen_port, args.listen_address)  # Initialized like this it is single-threaded/single-process
    ioloop = IOLoop.instance()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")
