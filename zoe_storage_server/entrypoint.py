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
