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

from io import BytesIO
import os

from zoe_storage_server.object_storage import ZoePersistentObjectStore


def test_application_data_upload(configuration):
    fake_data = BytesIO(b"test" * 1024)
    zos = ZoePersistentObjectStore(configuration.storage_path)
    filepath = os.path.join(zos.objects_path, "app-1.zip")
    zos.application_data_upload(1, fake_data)
    assert os.path.exists(filepath)
    data = zos.application_data_download(1)
    assert data == fake_data.getvalue()
    zos.application_data_delete(1)
    assert not os.path.exists(filepath)


def test_logs_upload(configuration):
    fake_data = BytesIO(b"test" * 1024)
    zos = ZoePersistentObjectStore(configuration.storage_path)
    filepath = os.path.join(zos.objects_path, "log-1.zip")
    zos.logs_archive_upload(1, fake_data)
    assert os.path.exists(filepath)
    data = zos.logs_archive_download(1)
    assert data == fake_data.getvalue()
    zos.logs_archive_delete(1)
    assert not os.path.exists(filepath)
