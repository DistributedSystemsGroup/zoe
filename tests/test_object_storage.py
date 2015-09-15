from zoe_scheduler.object_storage import *

fake_data = "test" * 1024


def test_application_data_upload():
    ret = init_history_paths()
    assert ret == True

