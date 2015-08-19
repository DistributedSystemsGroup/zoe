import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback

from caaas import app
from caaas.cleanup_thread import cleanup_task
from caaas.config_parser import config

DEBUG = True
log = logging.getLogger("caaas")


def main():
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("tornado").setLevel(logging.WARNING)

    print("Starting app...")
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(4000, "0.0.0.0")
    ioloop = IOLoop.instance()
    PeriodicCallback(cleanup_task, int(config.cleanup_thread_interval) * 1000).start()
    ioloop.start()


if __name__ == "__main__":
    main()
