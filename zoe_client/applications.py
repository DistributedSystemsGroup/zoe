import logging

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.lib.ipc import ZoeIPCClient
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.state import session
from zoe_client.state.application import ApplicationState
from zoe_client.users import user_check
from zoe_client.executions import execution_delete

from common.application_description import ZoeApplication
from common.exceptions import InvalidApplicationDescription
import common.zoe_storage_client as storage

log = logging.getLogger(__name__)


def _check_application(state, application_id: int):
    app_count = state.query(ApplicationState).filter_by(id=application_id).count()
    return app_count == 1


def application_binary_get(application_id: int) -> bytes:
    with session() as state:
        if _check_application(state, application_id):
            return storage.get(application_id, "apps")
        else:
            return None


def application_binary_put(application_id: int, bin_data: bytes):
    with session() as state:
        if _check_application(state, application_id):
            storage.put(application_id, "apps", bin_data)
        else:
            log.error("Trying to upload application data for non-existent application")


def application_executions_get(application_id) -> list:
    ipc_client = ZoeIPCClient()
    answer = ipc_client.ask("application_executions_get", application_id=application_id)
    if answer is None:
        return []
    return [Execution(e) for e in answer["executions"]]


def application_get(application_id):
    with session() as state:
        try:
            application = state.query(ApplicationState).filter_by(id=application_id).one()
        except NoResultFound:
            return None
        else:
            return application


def application_list(user_id: int) -> list:
    """
    Returns a list of all applications belonging to user_id
    :param user_id: the user
    :returns a list of ApplicationState objects
    """
    if not user_check(user_id):
        log.error("no such user")
        return None
    with session() as state:
        return state.query(ApplicationState).filter_by(user_id=user_id).all()


def application_new(user_id: int, description: ZoeApplication) -> ApplicationState:
    if not user_check(user_id):
        log.error("no such user")
        return None

    with session() as state:
        application = ApplicationState(user_id=user_id, description=description)
        state.add(application)
        state.commit()
        return application


def application_remove(application_id: int):
    with session() as state:
        if not _check_application(state, application_id):
            log.error("Trying to remove a non-existent application")
            return

        ipc_client = ZoeIPCClient()
        answer = ipc_client.ask("application_executions_get", application_id=application_id)
        if answer is None:
            return
        executions = [Execution(e) for e in answer["executions"]]
        for e in executions:
            execution_delete(e.id)

        application = state.query(ApplicationState).filter_by(id=application_id).one()
        storage.delete(application_id, "apps")
        state.delete(application)
        state.commit()
