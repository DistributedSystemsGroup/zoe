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

from argparse import ArgumentParser, Namespace
import logging
import http.server

from common.configuration import conf_init, zoe_conf
from zoe_storage_server.http_handler import ZoeObjectStoreHTTPRequestHandler

log = logging.getLogger(__name__)


def process_arguments() -> Namespace:
    argparser = ArgumentParser(description="Zoe Storage - Container Analytics as a Service storage component")
    argparser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')

    return argparser.parse_args()


def object_server():
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('requests').setLevel(logging.WARNING)

    conf_init()

    log.info("Object server listening on %s:%d" % (zoe_conf().http_listen_address, zoe_conf().http_listen_port))
    httpd = http.server.HTTPServer((zoe_conf().http_listen_address, zoe_conf().http_listen_port), ZoeObjectStoreHTTPRequestHandler)
    httpd.timeout = 1
    httpd.allow_reuse_address = True
    httpd.serve_forever()
