import swiftclient
from zoe_web.config_parser import config


class SwiftObjectStore:
    def __init__(self):
        self.log_container = config.swift_log_container_name
        self.app_container = config.swift_app_container_name
        self.username = config.swift_username
        self.password = config.swift_password
        self.tenant_name = config.swift_tenant_name
        self.auth_url = config.swift_keystone_auth_url

    def _connect(self) -> swiftclient.Connection:
        return swiftclient.client.Connection(auth_version='2',
                                             user=self.username,
                                             key=self.password,
                                             tenant_name=self.tenant_name,
                                             authurl=self.auth_url)

    def put_log(self, execution_id, log_data):
        swift = self._connect()
        swift.put_object(self.log_container, execution_id + ".zip", log_data)
        swift.close()

    def get_log(self, execution_id):
        swift = self._connect()
        log_data = swift.get_object(self.log_container, execution_id + ".zip")
        swift.close()
        return log_data

    def delete_log(self, execution_id):
        swift = self._connect()
        swift.delete_object(self.log_container, execution_id + ".zip")
        swift.close()

    def put_app(self, app_id, app_data):
        swift = self._connect()
        swift.put_object(self.app_container, app_id + ".zip", app_data)
        swift.close()

    def get_app(self, app_id):
        swift = self._connect()
        app_data = swift.get_object(self.app_container, app_id + ".zip")
        swift.close()
        return app_data

    def delete_app(self, app_id):
        swift = self._connect()
        swift.delete_object(self.app_container, app_id + ".zip")
        swift.close()
