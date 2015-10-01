import logging

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.lib.ipc import ZoeIPCClient
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.state import session
from zoe_client.state.application import ApplicationState

log = logging.getLogger(__name__)


def execution_delete(execution_id: int) -> None:
    ipc_client = ZoeIPCClient()
    ret = ipc_client.ask('execution_delete', execution_id=execution_id)
    return ret is not None


def execution_kill(execution_id: int) -> None:
    ipc_client = ZoeIPCClient()
    ret = ipc_client.ask('execution_kill', execution_id=execution_id)
    return ret is not None


def execution_get(execution_id: int) -> Execution:
    ipc_client = ZoeIPCClient()
    answer = ipc_client.ask('execution_get', execution_id=execution_id)
    if answer is not None:
        return Execution(answer["execution"])


def execution_start(application_id: int) -> Execution:
    with session() as state:
        try:
            application = state.query(ApplicationState).filter_by(id=application_id).one()
            assert isinstance(application, ApplicationState)
        except NoResultFound:
            log.error("No such application")
            return None

        ipc_client = ZoeIPCClient()
        answer = ipc_client.ask('execution_start', application_id=application_id, description=application.description.to_dict())
        if answer is not None:
            return Execution(answer["execution"])
        else:
            log.error("Application description failed the scheduler validation")
            return None
