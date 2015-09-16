from zoe_scheduler.object_storage import *

fake_data = b"test" * 1024


def test_application_data_upload(application):
    ret = init_history_paths()
    assert ret is True
    application_data_upload(application, fake_data)
    data = application_data_download(application)
    assert data == fake_data
    application_data_delete(application)
