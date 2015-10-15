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
This module contains all application execution-related API calls for Zoe clients.

Executions are the domain of the Zoe Scheduler, so all calls in this module require
IPC to the Zoe Scheduler.
"""

import logging

from sqlalchemy.orm.exc import NoResultFound

from zoe_client.lib.ipc import ZoeIPCClient
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.state import session
from zoe_client.state.application import ApplicationState

log = logging.getLogger(__name__)


def execution_delete(execution_id: int) -> bool:
    """
    Deletes an execution. If it is running it will be forcibly terminated.

    :param execution_id: the execution to delete
    :return: True is the operation was successful, False otherwise
    """
    ipc_client = ZoeIPCClient()
    ret = ipc_client.ask('execution_delete', execution_id=execution_id)
    return ret is not None


def execution_kill(execution_id: int) -> None:
    """
    Kills a running execution.

    :param execution_id: the execution to terminate
    :return: True is the operation was successful, False otherwise
    """
    ipc_client = ZoeIPCClient()
    ret = ipc_client.ask('execution_kill', execution_id=execution_id)
    return ret is not None


def execution_get(execution_id: int) -> Execution:
    """
    Retrieve the Execution object for an existing execution.

    :param execution_id: the execution to load from the scheduler
    :return: the Execution object, or None
    """
    ipc_client = ZoeIPCClient()
    answer = ipc_client.ask('execution_get', execution_id=execution_id)
    if answer is not None:
        return Execution(answer["execution"])


def execution_start(application_id: int) -> Execution:
    """
    Submit an application to the scheduler to start a new execution.

    :param application_id: the application to start
    :return: the new Execution object, or None in case of error
    """
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
