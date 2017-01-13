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

from zoe_lib.config import get_conf
from zoe_lib.state import Execution, Service

from zoe_master.backends.base import BaseBackend
from zoe_master.backends.old_swarm.backend import OldSwarmBackend

log = logging.getLogger(__name__)

_backend_initialized = False


def _get_backend() -> BaseBackend:
    backend_name = get_conf().backend
    if backend_name == 'OldSwarm':
        return OldSwarmBackend(get_conf())
    else:
        log.error('Unknown backend selected')
        assert False


def initialize_backend(state):
    """Initializes the configured backend."""
    assert not _backend_initialized
    backend = _get_backend()
    backend.init(state)


def shutdown_backend():
    """Shuts down the configured backend."""
    assert _backend_initialized
    backend = _get_backend()
    backend.shutdown()


def execution_to_containers(execution: Execution) -> None:
    """Translate an execution object into containers.

    If an error occurs some containers may have been created and needs to be cleaned-up.
    In case of error exceptions are raised.
    """
    backend = _get_backend()

    ordered_service_list = sorted(execution.services, key=lambda x: x.startup_order)

    env_subst_dict = {
        'execution_id': execution.id,
        "execution_name": execution.name,
        'user_name': execution.user_id,
        'deployment_name': get_conf().deployment_name,
    }

    for service in ordered_service_list:
        env_subst_dict['dns_name#' + service.name] = service.dns_name

    for service in ordered_service_list:
        env_subst_dict['dns_name#self'] = service.dns_name
        service.set_starting()
        backend.spawn_service(execution, service, env_subst_dict)


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
