import base64
import logging

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.state import AlchemySession
from zoe_client.ipc import ZoeIPCClient
from zoe_client.entities import Execution, Application, User
from zoe_client.state.user import UserState

log = logging.getLogger(__name__)


class ZoeClient:
    def __init__(self, ipc_server='localhost', ipc_port=8723):
        self.ipc_server = ZoeIPCClient(ipc_server, ipc_port)
        self.state = AlchemySession()

    # Applications
    def application_binary_put(self, application_id: int, app_data: bytes) -> bool:
        file_data = base64.b64encode(app_data)
        answer = self.ipc_server.ask('application_binary_put', application_id=application_id, bin_data=file_data)
        return answer is not None

    def application_binary_get(self, application_id: int) -> bytes:
        data = self.ipc_server.ask('application_binary_get', application_id=application_id)
        app_data = base64.b64decode(data['zip_data'])
        return app_data

    def application_list(self, user_id):
        """
        Returns a list of all Applications belonging to user_id
        :type user_id: int
        :rtype : list[Application]
        """
        answer = self.ipc_server.ask('application_list', user_id=user_id)
        if answer is None:
            return []
        else:
            return [Application(x) for x in answer['apps']]

    def application_new(self, user_id: int, description: dict) -> int:
        if not self.user_check(user_id):
            return None
        answer = self.ipc_server.ask('application_new', user_id=user_id, description=description)
        if answer is not None:
            return answer['application_id']

    def application_remove(self, application_id: int, force: bool) -> bool:
        answer = self.ipc_server.ask('application_remove', application_id=application_id, force=force)
        return answer is not None

    def application_start(self, application_id: int) -> int:
        answer = self.ipc_server.ask('application_start', application_id=application_id)
        if answer is not None:
            return answer["execution_id"]
        else:
            return None

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

    def execution_get(self, execution_id: int) -> Execution:
        exec_dict = self.ipc_server.ask('execution_get', execution_id=execution_id)
        if exec_dict is not None:
            return Execution(exec_dict)

    def execution_terminate(self, execution_id: int) -> None:
        ret = self.ipc_server.ask('execution_terminate', execution_id=execution_id)
        return ret is not None

    # Logs
    def log_get(self, container_id: int) -> str:
        clog = self.ipc_server.ask('log_get', container_id=container_id)
        if clog is not None:
            return clog['log']

    def log_history_get(self, execution_id):
        data = self.ipc_server.ask('log_history_get', execution_id=execution_id)
        log_data = base64.b64decode(data['zip_data'])
        return log_data

    # Platform
    def platform_stats(self) -> dict:
        stats = self.ipc_server.ask('platform_stats')
        return stats

    # Users
    def user_check(self, user_id: int) -> bool:
        num = self.state.query(UserState).filter_by(id=user_id).count()
        return num == 1

    def user_new(self, email: str) -> User:
        user = UserState(email=email)
        self.state.add(user)
        self.state.commit()
        return User(user.to_dict())

    def user_get(self, user_id: int) -> User:
        try:
            user = self.state.query(UserState).filter_by(id=user_id).one()
        except NoResultFound:
            return None
        return User(user.to_dict())

    def user_get_by_email(self, email: str) -> User:
        try:
            user = self.state.query(UserState).filter_by(email=email).one()
        except NoResultFound:
            return None
        else:
            return User(user.to_dict())
