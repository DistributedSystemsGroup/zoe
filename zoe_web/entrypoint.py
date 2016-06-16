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

from flask import Flask
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

import zoe_web.config as config
import zoe_web.db_init
import zoe_web.api_endpoint
import zoe_web.rest_api
import zoe_web.web

log = logging.getLogger("zoe_web")
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(name)s (%(threadName)s): %(message)s'


def zoe_web_main() -> int:
    """
    This is the entry point for the Zoe Web script.
    :return: int
    """
    config.load_configuration()
    args = config.get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.DEBUG)

    log.info("Starting HTTP server...")
    app = Flask(__name__, static_url_path='/does-not-exist')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    app.register_blueprint(zoe_web.rest_api.api_init())
    app.register_blueprint(zoe_web.web.web_init())

    zoe_web.db_init.init()

    config.api_endpoint = zoe_web.api_endpoint.APIEndpoint()

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(args.listen_port, args.listen_address)
    ioloop = IOLoop.instance()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")
