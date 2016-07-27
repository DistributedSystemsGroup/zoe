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
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import Application

import zoe_lib.config as config
import zoe_api.db_init
import zoe_api.api_endpoint
import zoe_api.rest_api
import zoe_api.web
import zoe_api.auth.ldap
from zoe_api.web.custom_request_handler import JinjaApp

log = logging.getLogger("zoe_api")
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

    if config.get_conf().auth_type == 'ldap' and not zoe_api.auth.ldap.LDAP_AVAILABLE:
        log.error("LDAP authentication requested, but 'pyldap' module not installed.")
        return 1

    zoe_api.db_init.init()

    api_endpoint = zoe_api.api_endpoint.APIEndpoint()

    app_settings = {
        'static_path': os.path.join(os.path.dirname(__file__), "web", "static"),
        'template_path': os.path.join(os.path.dirname(__file__), "web", "templates"),
        'debug': args.debug
    }
    app = Application(zoe_api.web.web_init(api_endpoint) + zoe_api.rest_api.api_init(api_endpoint), **app_settings)
    JinjaApp.init_app(app)

    log.info("Starting HTTP server...")
    http_server = HTTPServer(app)
    http_server.bind(args.listen_port, args.listen_address)
    http_server.start(num_processes=1)

    retry_cb = PeriodicCallback(api_endpoint.retry_submit_error_executions, 30000)
    retry_cb.start()

    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")

    return 0
