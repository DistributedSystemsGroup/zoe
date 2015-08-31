import logging
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback

from zoe_web import app
from zoe_web.emails import email_task

from common.configuration import conf

DEBUG = True
log = logging.getLogger("zoe_web")


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
    PeriodicCallback(email_task, int(conf["email_task_interval"]) * 1000).start()
    ioloop.start()


if __name__ == "__main__":
    main()
