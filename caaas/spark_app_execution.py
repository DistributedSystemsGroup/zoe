from zipfile import ZipFile
import os
import shutil

from caaas.sql import CAaaState
from caaas.config_parser import config


class AppHistory:
    def __init__(self, user_id):
        self.base_path = config.history_storage_path
        self.per_user_max_count = int(config.history_per_user_count)
        self.user_id = str(user_id)

    def _app_path(self, app_id):
        return os.path.join(self.base_path, self.user_id, str(app_id))

    def _delete_app_history(self, app_id):
        app_path = self._app_path(app_id)
        shutil.rmtree(app_path)

    def cleanup(self):
        state = CAaaState()
        num_apps = state.count_apps_finished(self.user_id)
        if num_apps > self.per_user_max_count:
            app_id = state.remove_oldest_application(self.user_id)
            self._delete_app_history(app_id)

    def add_application_zip(self, app_id, file_data):
        app_path = self._app_path(app_id)
        if not os.path.exists(app_path):
            os.makedirs(app_path)
        file_data.save(os.path.join(app_path, "app.zip"))

    def save_log(self, app_id, logname, log):
        app_path = self._app_path(app_id)
        assert os.path.exists(app_path)
        zip_path = os.path.join(app_path, "logs.zip")
        z = ZipFile(zip_path, mode="a")
        z.writestr(logname + ".txt", log)
        z.close()

    def get_log_archive_path(self, app_id):
        app_path = self._app_path(app_id)
        zip_path = os.path.join(app_path, "logs.zip")
        if not os.path.exists(app_path):
            return None
        else:
            return zip_path


def application_submitted(user_id, execution_name, spark_options, commandline, file_data) -> int:
    ah = AppHistory(user_id)
    ah.cleanup()
    state = CAaaState()
    app_id = state.new_application(user_id, execution_name, spark_options, commandline)
    ah.add_application_zip(app_id, file_data)
    return app_id


def setup_volume(user_id, app_id, app_pkg):
    app_pkg = ZipFile(app_pkg)
    exec_path = config.docker_volume_path
    exec_path = os.path.join(exec_path, str(user_id), str(app_id))
    os.makedirs(exec_path)
    app_pkg.extractall(exec_path)
    state = CAaaState()
    state.application_ready(app_id)
