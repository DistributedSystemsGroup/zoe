from io import BytesIO
import logging
import zipfile

import requests
import requests.exceptions

from common.configuration import zoe_conf

log = logging.getLogger(__name__)


def generate_application_binary_url(application_id: int) -> str:
    return zoe_conf().object_storage_url + '/apps/{}'.format(application_id)


def _upload(obj_id, kind, data: bytes):
    url = zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)
    files = {'file': data}
    try:
        requests.post(url, files=files)
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to {} to POST the binary file".format(url))


def _download(obj_id, kind) -> bytes:
    url = zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to {} to GET the binary file".format(url))
        return None
    else:
        return r.content


def _delete(obj_id, kind):
    url = zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)
    try:
        requests.delete(url)
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to {} to DELETE the binary file".format(url))


def upload_application(app_id, app_data: bytes):
    _upload(app_id, "apps", app_data)


def download_application(application_id) -> bytes:
    return _download(application_id, "apps")


def download_log_url(execution_id) -> bytes:
    return zoe_conf().object_storage_url + '/logs/{}'.format(execution_id)


def delete_application(application_id):
    _delete(application_id, "apps")


def logs_archive_create(execution_id: int, logs: list):
    zipdata = BytesIO()
    with zipfile.ZipFile(zipdata, "w", compression=zipfile.ZIP_DEFLATED) as logzip:
        for c in logs:
            fname = c[0] + "-" + c[1] + ".txt"
            logzip.writestr(fname, c[2])
    _upload(execution_id, "logs", zipdata)
