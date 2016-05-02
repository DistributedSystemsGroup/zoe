# Copyright (c) 2015, Daniele Venzano
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

from zoe_web import app
from zoe_web.config import load_configuration, get_conf

log = logging.getLogger("zoe_web")
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(name)s (%(threadName)s): %(message)s'


def zoe_web_main() -> int:
    """
    This is the entry point for the Zoe Web script.
    :return: int
    """
    load_configuration()
    args = get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.DEBUG)

    log.info("Starting HTTP server...")
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.secret_key = args.cookie_secret

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(args.listen_port, args.listen_address)
    ioloop = IOLoop.instance()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")
