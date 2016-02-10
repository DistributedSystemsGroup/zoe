# Copyright (c) 2016, Daniele Venzano
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

import logging
import os

from zoe_scheduler.state.blobs import BaseBlobs
from zoe_scheduler.config import get_conf

BLOB_PATH = 'blobs'

log = logging.getLogger(__name__)


class FSBlobs(BaseBlobs):
    def init(self):
        state_path = get_conf().state_dir
        self.blob_path = os.path.join(state_path, BLOB_PATH)
        try:
            os.makedirs(self.blob_path, exist_ok=True)
        except PermissionError:
            log.error('Permission denied trying to create the directory {}'.format(self.blob_path))

    def store_blob(self, kind, name, data: bytes):
        path = os.path.join(self.blob_path, kind)
        os.makedirs(path, exist_ok=True)
        open(os.path.join(path, name), "wb").write(data)

    def load_blob(self, kind, name) -> bytes:
        path = os.path.join(self.blob_path, kind)
        try:
            data = open(os.path.join(path, name), "rb").read()
        except OSError:
            log.error('Trying to open a blog that is not there: {} {}'.format(kind, name))
            return None
        return data

    def delete_blob(self, kind, name):
        path = os.path.join(self.blob_path, kind, name)
        try:
            os.unlink(path)
        except OSError:
            log.warning('Trying to delete a blob that is not there: {} {}'.format(kind, name))

    def list_blobs(self, kind):
        path = os.path.join(self.blob_path, kind)
        try:
            files = os.listdir(path)
        except OSError:
            return []
        return [f for f in files if f != '..' and f != '.']
