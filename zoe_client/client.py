import logging

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.lib.ipc import ZoeIPCClient
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.state import session
from zoe_client.state.application import ApplicationState
import zoe_client.zoe_storage_client as storage

log = logging.getLogger(__name__)


class ZoeClient:
    def __init__(self, ipc_server='localhost', ipc_port=8723):
        self.ipc_server = ZoeIPCClient(ipc_server, ipc_port)
        self.state = session()

    def _check_application(self, application_id: int):
        app_count = self.state.query(ApplicationState).filter_by(id=application_id).count()
        return app_count == 1

    # Applications
    def application_binary_get(self, application_id: int) -> bytes:
        if self._check_application(application_id):
            return storage.download_application(application_id)
        else:
            return None

    def application_binary_put(self, application_id: int, bin_data: bytes):
        if self._check_application(application_id):
            storage.upload_application(application_id, bin_data)
        else:
            log.error("Trying to upload application data for non-existent application")

    def application_executions_get(self, application_id) -> list:
        answer = self.ipc_server.ask("application_executions_get", application_id=application_id)
        if answer is None:
            return []
        return [Execution(e) for e in answer["executions"]]

    def application_get(self, application_id):
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return None
        else:
            return application

    def application_list(self, user_id: int) -> list:
        """
        Returns a list of all applications belonging to user_id
        :param user_id: the user
        :returns a list of ApplicationState objects
        """
        return self.state.query(ApplicationState).filter_by(user_id=user_id).all()

    def application_new(self, user_id: int, description: dict) -> ApplicationState:
        answer = self.ipc_server.ask('application_validate', description=description)
        if answer is None:
            log.error("Application description failed the scheduler validation")
            return None

        application = ApplicationState(user_id=user_id, description=description)
        self.state.add(application)
        self.state.commit()
        return application

    def application_remove(self, application_id: int):
        if not self._check_application(application_id):
            log.error("Trying to remove a non-existent application")
            return

        answer = self.ipc_server.ask("application_executions_get", application_id=application_id)
        if answer is None:
            return
        executions = [Execution(e) for e in answer["executions"]]
        for e in executions:
            self.execution_delete(e.id)

        application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        storage.delete_application(application_id)
        self.state.delete(application)
        self.state.commit()

    def application_validate(self, description: dict) -> bool:
        answer = self.ipc_server.ask('application_validate', description=description)
        return answer is not None

    # Containers
    def container_stats(self, container_id):
        return self.ipc_server.ask('container_stats', container_id=container_id)

    # Executions
    def execution_delete(self, execution_id: int) -> None:
        ret = self.ipc_server.ask('execution_delete', execution_id=execution_id)
        return ret is not None

    def execution_kill(self, execution_id: int) -> None:
        ret = self.ipc_server.ask('execution_kill', execution_id=execution_id)
        return ret is not None

    def execution_get(self, execution_id: int) -> Execution:
        answer = self.ipc_server.ask('execution_get', execution_id=execution_id)
        if answer is not None:
            return Execution(answer["execution"])

    def execution_start(self, application_id: int) -> Execution:
        try:
            application = self.state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            log.error("No such application")
            return None

        answer = self.ipc_server.ask('application_validate', description=application.description)
        if answer is None:
            log.error("Application description failed the scheduler validation")
            return None

        answer = self.ipc_server.ask('execution_start', application_id=application_id, description=application.description)
        if answer is not None:
            return Execution(answer["execution"])
        else:
            return None

    # Logs
    def log_get(self, container_id: int) -> str:
        answer = self.ipc_server.ask('log_get', container_id=container_id)
        if answer is not None:
            return answer['log']

    # Platform
    def platform_stats(self) -> dict:
        stats = self.ipc_server.ask('platform_stats')
        return stats
