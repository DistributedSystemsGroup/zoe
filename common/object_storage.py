import os
import logging

from common.state import Application, Execution
from common.configuration import zoeconf

log = logging.getLogger(__name__)


def init_history_paths() -> bool:
    if not os.path.exists(zoeconf.history_path):
        try:
            os.makedirs(zoeconf.history_path)
        except OSError:
            log.error("Cannot create history directory in {}".format(zoeconf.history_path))
            return False
        os.makedirs(os.path.join(zoeconf.history_path, 'apps'))
        os.makedirs(os.path.join(zoeconf.history_path, 'logs'))
    return True


def application_data_upload(application: Application, data: bytes) -> bool:
    fpath = os.path.join(zoeconf.history_path, 'apps', 'app-{}.zip'.format(application.id))
    open(fpath, "wb").write(data)


def application_data_download(application: Application) -> bytes:
    fpath = os.path.join(zoeconf.history_path, 'apps', 'app-{}.zip'.format(application.id))
    data = open(fpath, "rb").read()
    return data


def application_data_delete(application: Application):
    fpath = os.path.join(zoeconf.history_path, 'apps', 'app-{}.zip'.format(application.id))
    try:
        os.unlink(fpath)
    except OSError:
        log.warning("Binary data for application {} not found, cannot delete".format(application.id))


def logs_archive_upload(execution: Execution, data: bytes) -> bool:
    fpath = os.path.join(zoeconf.history_path, 'logs', 'log-{}.zip'.format(execution.id))
    open(fpath, "wb").write(data)


def logs_archive_download(execution: Execution) -> bytes:
    fpath = os.path.join(zoeconf.history_path, 'logs', 'log-{}.zip'.format(execution.id))
    data = open(fpath, "rb").read()
    return data


def logs_archive_delete(execution: Execution):
    fpath = os.path.join(zoeconf.history_path, 'logs', 'log-{}.zip'.format(execution.id))
    try:
        os.unlink(fpath)
    except OSError:
        log.warning("Logs archive for execution {} not found, cannot delete".format(execution.id))
