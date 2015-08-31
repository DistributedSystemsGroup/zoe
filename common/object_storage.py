import redis

from common.state import Application, Execution
from common.configuration import conf


def _connect():
    server = conf["redis_server"]
    port = conf["redis_port"]
    db = conf["redis_db"]
    return redis.StrictRedis(host=server, port=port, db=db)


def application_data_upload(application: Application, data: bytes) -> bool:
    r = _connect()
    key = "app-{}".format(application.id)
    r.set(key, data)


def application_data_download(application: Application) -> bytes:
    r = _connect()
    key = "app-{}".format(application.id)
    return r.get(key)


def application_data_delete(application: Application):
    r = _connect()
    key = "app-{}".format(application.id)
    r.delete(key)


def logs_archive_upload(execution: Execution, data: bytes) -> bool:
    r = _connect()
    key = "log-{}".format(execution.id)
    r.set(key, data)


def logs_archive_download(execution: Execution) -> bytes:
    r = _connect()
    key = "log-{}".format(execution.id)
    return r.get(key)


def logs_archive_delete(execution: Execution):
    r = _connect()
    key = "log-{}".format(execution.id)
    r.delete(key)
