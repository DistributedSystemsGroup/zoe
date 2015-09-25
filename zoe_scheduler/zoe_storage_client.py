from io import BytesIO
import logging
import zipfile

import requests
import requests.exceptions

from common.configuration import zoe_conf

log = logging.getLogger(__name__)


def generate_application_binary_url(application_id: int) -> str:
    return zoe_conf().object_storage_url + '/apps/{}'.format(application_id)


def _upload_logdata(execution_id, logdata):
    url = zoe_conf().object_storage_url + '/logs/{}'.format(execution_id)
    files = {'file': logdata}
    try:
        requests.post(url, files=files)
    except requests.exceptions.ConnectionError:
        log.error("cannot upload log archive, logs will be lost!")


def logs_archive_create(execution_id: int, logs: list):
    zipdata = BytesIO()
    with zipfile.ZipFile(zipdata, "w", compression=zipfile.ZIP_DEFLATED) as logzip:
        for c in logs:
            fname = c[0] + "-" + c[1] + ".txt"
            logzip.writestr(fname, c[2])
    _upload_logdata(execution_id, zipdata.getvalue())
