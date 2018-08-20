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

"""Zoe API entrypoint module."""

import logging
import os

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

import zoe_lib.config
import zoe_lib.state
import zoe_api.api_endpoint
import zoe_api.rest_api
import zoe_api.master_api
import zoe_api.web
import zoe_api.auth.ldap
from zoe_api.web.request_handler import JinjaApp

log = logging.getLogger("zoe_api")
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(threadName)s->%(name)s: %(message)s'


def zoe_web_main(test_conf=None) -> int:
    """
    This is the entry point for the Zoe Web script.
    :return: int
    """
    zoe_lib.config.load_configuration(test_conf)
    args = zoe_lib.config.get_conf()

    log_args = {
        'level': logging.DEBUG if args.debug else logging.INFO,
        'format': LOG_FORMAT
    }
    if args.log_file != "stderr":
        log_args['filename'] = args.log_file
    logging.basicConfig(**log_args)
    logging.getLogger("MARKDOWN").setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.WARNING)

    sql_manager = zoe_lib.state.SQLManager(zoe_lib.config.get_conf())
    sql_manager.init_db()

    master_api = zoe_api.master_api.APIManager()
    api_endpoint = zoe_api.api_endpoint.APIEndpoint(master_api, sql_manager)

    app_settings = {
        'static_path': os.path.join(os.path.dirname(__file__), "web", "static"),
        'template_path': os.path.join(os.path.dirname(__file__), "web", "templates"),
        'cookie_secret': zoe_lib.config.get_conf().cookie_secret,
        'login_url': '/login',
        'debug': args.debug
    }
    app = Application(zoe_api.web.web_init(api_endpoint) + zoe_api.rest_api.api_init(api_endpoint), **app_settings)
    JinjaApp.init_app(app)

    log.info("Starting HTTP server...")
    http_server = HTTPServer(app)
    http_server.bind(args.listen_port, args.listen_address)
    http_server.start(num_processes=1)

    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")

    return 0
