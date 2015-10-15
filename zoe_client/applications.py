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

"""
This module all application-related API calls for Zoe clients.

Applications are tracked by client code, in the client database. The Zoe scheduler component
will receive a valid application description and has no need to access or modify the
application state.
"""

import logging

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.lib.ipc import ZoeIPCClient
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.state import session
from zoe_client.state.application import ApplicationState
from zoe_client.users import user_check
from zoe_client.executions import execution_delete

from common.application_description import ZoeApplication
import common.zoe_storage_client as storage

log = logging.getLogger(__name__)


def _check_application(state, application_id: int):
    """
    Convenience function to check if a given application_id is valid.

    :param state: SQLAlchemy session
    :param application_id: the application ID to check
    :return: True if application exists, False otherwise
    """
    app_count = state.query(ApplicationState).filter_by(id=application_id).count()
    return app_count == 1


def application_binary_get(application_id: int) -> bytes:
    """
    Retrieves the binary data associated with an application.

    :param application_id: the application identifier used to store the binary data
    :return: the binary data, or None
    """
    with session() as state:
        if _check_application(state, application_id):
            return storage.get(application_id, "apps")
        else:
            return None


def application_binary_put(application_id: int, bin_data: bytes):
    """
    Stores binary data associated with an application.

    :param application_id: the application identifier
    :param bin_data: the binary data to store
    """
    with session() as state:
        if _check_application(state, application_id):
            storage.put(application_id, "apps", bin_data)
        else:
            log.error("Trying to upload application data for non-existent application")


def application_executions_get(application_id) -> list:
    """
    Return a list of Execution objects for a given application.
    This call will use IPC to talk to the Zoe Scheduler.

    :param application_id: the application identifier
    :return: a list of Execution objects, empty in case of error
    """
    ipc_client = ZoeIPCClient()
    answer = ipc_client.ask("application_executions_get", application_id=application_id)
    if answer is None:
        return []
    return [Execution(e) for e in answer["executions"]]


def application_get(application_id):
    """
    Return an Application object

    :param application_id: the identifier of the application
    :return: the Application SQLAlchemy object
    """
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
    :return: a list of ApplicationState objects
    """
    if not user_check(user_id):
        log.error("no such user")
        return None
    with session() as state:
        return state.query(ApplicationState).filter_by(user_id=user_id).all()


def application_new(user_id: int, description: ZoeApplication) -> ApplicationState:
    """
    Create a new application and commit it to the database.

    :param user_id: the user_id that owns this application
    :param description: the application description
    :return: the SQLAlchemy Application object
    """
    if not user_check(user_id):
        log.error("no such user")
        return None

    with session() as state:
        application = ApplicationState(user_id=user_id, description=description)
        state.add(application)
        state.commit()
        return application


def application_remove(application_id: int):
    """
    Deletes an application, its executions and its binary data.
    This call will use IPC to talk to the Zoe Scheduler.
    If the application does not exists an error will be logged.

    :param application_id: the application to delete
    """
    with session() as state:
        if not _check_application(state, application_id):
            log.error("Trying to remove a non-existent application")
            return

        ipc_client = ZoeIPCClient()
        answer = ipc_client.ask("application_executions_get", application_id=application_id)
        if answer is not None:
            executions = [Execution(e) for e in answer["executions"]]
            for e in executions:
                execution_delete(e.id)

        application = state.query(ApplicationState).filter_by(id=application_id).one()
        storage.delete(application_id, "apps")
        state.delete(application)
        state.commit()
