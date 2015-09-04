#!/usr/bin/env python3

import argparse
import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback

from zoe_web import app

from common.configuration import conf

log = logging.getLogger("zoe_web")


def process_arguments() -> argparse.Namespace:
    argparser = argparse.ArgumentParser(description="Zoe Web - Container Analytics as a Service web client")
    argparser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
    argparser.add_argument('--rpyc-server', default=None, help='Specify an RPyC server instead of using autodiscovery')
    argparser.add_argument('--rpyc-port', default=4000, type=int, help='Specify an RPyC server port, default is 4000')

    return argparser.parse_args()


def main():
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.WARNING)

    if args.rpyc_server is None:
        conf['client_rpyc_autodiscovery'] = True
    else:
        conf['client_rpyc_autodiscovery'] = False
        conf['client_rpyc_server'] = args.rpyc_server
        conf['client_rpyc_port'] = args.rpyc_port

    log.info("Starting HTTP server...")
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000, "0.0.0.0")
    ioloop = IOLoop.instance()
#    PeriodicCallback(email_task, int(conf["email_task_interval"]) * 1000).start()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        print("CTRL-C detected, terminating")


if __name__ == "__main__":
    main()
