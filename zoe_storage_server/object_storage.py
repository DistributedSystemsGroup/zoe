# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from io import BufferedIOBase
import logging
import os
from shutil import copyfileobj

log = logging.getLogger(__name__)


class ZoePersistentObjectStore:
    def __init__(self, storage_path):
        self.base_path = storage_path
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
