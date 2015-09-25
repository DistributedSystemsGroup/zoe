from io import BufferedIOBase
import logging
import os
from shutil import copyfileobj

from zoe_storage_server.configuration import storage_conf

log = logging.getLogger(__name__)


class ZoePersistentObjectStore:
    def __init__(self):
        self.base_path = storage_conf().storage_path
        self.objects_path = os.path.join(self.base_path, 'objects')
        self._init_paths()

    def _init_paths(self):
        if not os.path.exists(self.base_path):
            log.error("Storage path does not exist: {}".format(self.base_path))
        if not os.path.exists(self.objects_path):
            os.makedirs(self.objects_path)

    def _write(self, key: str, data: BufferedIOBase):
        fpath = os.path.join(self.objects_path, key)
        with open(fpath, "wb") as fp:
            copyfileobj(data, fp)

    def _read(self, key: str):
        fpath = os.path.join(self.objects_path, key)
        try:
            data = open(fpath, "rb").read()
        except OSError:
            return None
        else:
            return data

    def _delete(self, key: str):
        fpath = os.path.join(self.objects_path, key)
        try:
            os.unlink(fpath)
        except OSError:
            log.warning("cannot delete object {}".format(key))

    def application_data_upload(self, application_id: int, data: BufferedIOBase):
        key = 'app-{}.zip'.format(application_id)
        self._write(key, data)

    def application_data_download(self, application_id: int) -> bytes:
        key = 'app-{}.zip'.format(application_id)
        return self._read(key)

    def application_data_delete(self, application_id: int):
        key = 'app-{}.zip'.format(application_id)
        self._delete(key)

    def logs_archive_upload(self, execution_id: int, data: BufferedIOBase):
        key = 'log-{}.zip'.format(execution_id)
        self._write(key, data)

    def logs_archive_download(self, execution_id: int) -> bytes:
        key = 'log-{}.zip'.format(execution_id)
        return self._read(key)

    def logs_archive_delete(self, execution_id: int):
        key = 'log-{}.zip'.format(execution_id)
        self._delete(key)
