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
