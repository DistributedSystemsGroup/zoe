# Copyright (c) 2017, Daniele Venzano
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

"""The high-level interface that Zoe uses to talk to the configured container backend."""

import logging
from typing import List

from zoe_lib.config import get_conf
from zoe_lib.state import Execution, Service

from zoe_master.backends.base import BaseBackend
from zoe_master.backends.service_instance import ServiceInstance
from zoe_master.backends.old_swarm.backend import OldSwarmBackend
import zoe_master.backends.old_swarm.api_client
from zoe_master.backends.old_swarm_new_api.backend import OldSwarmNewAPIBackend
import zoe_master.backends.old_swarm_new_api.api_client
from zoe_master.exceptions import ZoeStartExecutionFatalException, ZoeStartExecutionRetryException, ZoeException

log = logging.getLogger(__name__)


def _get_backend() -> BaseBackend:
    """Return the right backend instance by reading the global configuration."""
    backend_name = get_conf().backend
    if backend_name == 'OldSwarm':
        if not zoe_master.backends.old_swarm.api_client.AVAILABLE:
            raise ZoeException('The OldSwarm backend requires docker-py version <= 1.10.2')
        return OldSwarmBackend(get_conf())
    elif backend_name == 'OldSwarmNewAPI':
        if not zoe_master.backends.old_swarm_new_api.api_client.AVAILABLE:
            raise ZoeException('The OldSwarmNewAPI backend requires docker python version >= 2.0.2')
        return OldSwarmNewAPIBackend(get_conf())
    else:
        log.error('Unknown backend selected')
        assert False


def initialize_backend(state):
    """Initializes the configured backend."""
    backend = _get_backend()
    backend.init(state)


def shutdown_backend():
    """Shuts down the configured backend."""
    backend = _get_backend()
    backend.shutdown()


def service_list_to_containers(execution: Execution, service_list: List[Service]) -> str:
    """Given a subset of services from an execution, tries to start them, return one of 'ok', 'requeue' for temporary failures and 'fatal' for fatal failures."""
    backend = _get_backend()

    ordered_service_list = sorted(service_list, key=lambda x: x.startup_order)

    for service in ordered_service_list:
        service.set_starting()
        instance = ServiceInstance(execution, service)
        try:
            backend_id = backend.spawn_service(instance)
        except ZoeStartExecutionRetryException as ex:
            log.warning('Temporary failure starting service {} of execution {}: {}'.format(service.id, execution.id, ex.message))
            service.set_error(ex.message)
            execution.set_error_message(ex.message)
            terminate_execution(execution)
            execution.set_scheduled()
            return "requeue"
        except ZoeStartExecutionFatalException as ex:
            log.error('Fatal error trying to start service {} of execution {}: {}'.format(service.id, execution.id, ex.message))
            execution.set_error_message(ex.message)
            terminate_execution(execution)
            execution.set_error()
            return "fatal"
        except Exception as ex:
            log.error('Fatal error trying to start service {} of execution {}'.format(service.id, execution.id))
            log.exception('BUG, this error should have been caught earlier')
            execution.set_error_message(str(ex))
            terminate_execution(execution)
            execution.set_error()
            return "fatal"
        else:
            service.set_active(backend_id)

    return "ok"


def start_all(execution: Execution) -> str:
    """Translate an execution object into containers.

    If an error occurs some containers may have been created and needs to be cleaned-up.
    """
    log.debug('starting all services for execution {}'.format(execution.id))
    execution.set_starting()
    return service_list_to_containers(execution, execution.services)


def start_essential(execution) -> str:
    """Start the essential services for this execution"""
    log.debug('starting essential services for execution {}'.format(execution.id))
    execution.set_starting()

    return service_list_to_containers(execution, execution.essential_services)


def start_elastic(execution) -> str:
    """Start the runnable elastic services"""
    elastic_to_start = [s for s in execution.elastic_services if s.status == Service.RUNNABLE_STATUS]
    return service_list_to_containers(execution, elastic_to_start)


def terminate_execution(execution: Execution) -> None:
    """Terminate an execution."""
    execution.set_cleaning_up()
    backend = _get_backend()
    for service in execution.services:
        assert isinstance(service, Service)
        if service.backend_id is not None:
            service.set_terminating()
            backend.terminate_service(service)
            service.set_inactive()
            log.debug('Service {} terminated'.format(service.name))
    execution.set_terminated()


def get_platform_state():
    """Retrieves the state of the platform by querying the container backend. Platform state includes information on free/reserved resources for each node. This information is used for advanced scheduling."""
    backend = _get_backend()
    return backend.platform_state()


def get_service_log(service):
    """Retrieve the log (usually stdout/stderr) of the main processes running in the container."""
    backend = _get_backend()
    return backend.service_log(service)