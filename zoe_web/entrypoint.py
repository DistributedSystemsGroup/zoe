import argparse
import logging

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from zoe_web import app
from common.configuration import conf_init, zoe_conf
from zoe_client.state import init as state_init

log = logging.getLogger("zoe_web")


def process_arguments() -> argparse.Namespace:
    argparser = argparse.ArgumentParser(description="Zoe Web - Container Analytics as a Service web client")
    argparser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
    argparser.add_argument('--ipc-server', help='Address of the Zoe scheduler process')
    argparser.add_argument('--ipc-port', help='Port of the Zoe scheduler process')

    return argparser.parse_args()


def zoe_web() -> int:
    """
    This is the entry point for the Zoe Web script.
    :return: int
    """
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.WARNING)

    conf_init()
    if args.ipc_server is not None:
        zoe_conf().set('zoe_client', 'scheduler_ipc_address', args.ipc_server)
    if args.ipc_port is not None:
        zoe_conf().set('zoe_client', 'scheduler_ipc_port', args.ipc_port)

    state_init(zoe_conf().db_url)

    log.info("Starting HTTP server...")
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.secret_key = zoe_conf().cookies_secret_key

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000, "0.0.0.0")
    ioloop = IOLoop.instance()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")
