from io import BytesIO
import logging
import zipfile

import requests
import requests.exceptions

from common.configuration import zoe_conf

log = logging.getLogger(__name__)


def generate_storage_url(obj_id: int, kind: str) -> str:
    return zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)


def put(obj_id, kind, data: bytes):
    url = zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)
    files = {'file': data}
    try:
        requests.post(url, files=files)
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to {} to POST the binary file".format(url))


def get(obj_id, kind) -> bytes:
    url = zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to {} to GET the binary file".format(url))
        return None
    else:
        return r.content


def check(obj_id, kind) -> bool:
    url = zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)
    try:
        r = requests.head(url)
    except requests.exceptions.ConnectionError:
        return False
    else:
        return r.status_code == 200


def delete(obj_id, kind):
    url = zoe_conf().object_storage_url + '/{}/{}'.format(kind, obj_id)
    try:
        requests.delete(url)
    except requests.exceptions.ConnectionError:
        log.error("Cannot connect to {} to DELETE the binary file".format(url))


def logs_archive_create(execution_id: int, logs: list):
    zipdata = BytesIO()
    with zipfile.ZipFile(zipdata, "w", compression=zipfile.ZIP_DEFLATED) as logzip:
        for c in logs:
            fname = c[0] + "-" + c[1] + ".txt"
            logzip.writestr(fname, c[2])
    put(execution_id, "logs", zipdata.getvalue())
