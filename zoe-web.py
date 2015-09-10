#!/usr/bin/env python3

import argparse
import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from zoe_web import app

from common.configuration import ipcconf

log = logging.getLogger("zoe_web")


def process_arguments() -> argparse.Namespace:
    argparser = argparse.ArgumentParser(description="Zoe Web - Container Analytics as a Service web client")
    argparser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
    argparser.add_argument('--ipc-server', default='localhost', help='Address of the Zoe scheduler process')
    argparser.add_argument('--ipc-port', default=8723, type=int, help='Port of the Zoe scheduler process')

    return argparser.parse_args()


def main():
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("tornado").setLevel(logging.WARNING)

    ipcconf['server'] = args.ipc_server
    ipcconf['port'] = args.ipc_port

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
