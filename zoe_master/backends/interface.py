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
import time
from typing import List, Union

from zoe_lib.config import get_conf
from zoe_lib.state import Execution, Service  # pylint: disable=unused-import

from zoe_master.backends.base import BaseBackend
from zoe_master.backends.service_instance import ServiceInstance
from zoe_master.exceptions import ZoeStartExecutionFatalException, ZoeStartExecutionRetryException, ZoeException
from zoe_master.stats import ClusterStats  # pylint: disable=unused-import

try:
    from zoe_master.backends.kubernetes.backend import KubernetesBackend
except ImportError:
    KubernetesBackend = None

try:
    from zoe_master.backends.docker.backend import DockerEngineBackend
except ImportError:
    DockerEngineBackend = None

log = logging.getLogger(__name__)


def _get_backend() -> Union[BaseBackend, None]:
    """Return the right backend instance by reading the global configuration."""
    backend_name = get_conf().backend
    assert backend_name in ['Kubernetes', 'Swarm', 'DockerEngine']
    if backend_name == 'Kubernetes':
        if KubernetesBackend is None:
            raise ZoeException('The Kubernetes backend requires the pykube module')
        return KubernetesBackend(get_conf())
    elif backend_name == 'DockerEngine':
        if DockerEngineBackend is None:
            raise ZoeException('The Docker Engine backend requires docker python version >= 2.0.2')
        return DockerEngineBackend(get_conf())
    else:
        log.error('Unknown backend selected')
        return None


def initialize_backend(state):
    """Initializes the configured backend."""
    backend = _get_backend()
    backend.init(state)


def shutdown_backend():
    """Shuts down the configured backend."""
    backend = _get_backend()
    backend.shutdown()


def service_list_to_containers(execution: Execution, service_list: List[Service], placement=None) -> str:
    """Given a subset of services from an execution, tries to start them, return one of 'ok', 'requeue' for temporary failures and 'fatal' for fatal failures."""
    backend = _get_backend()

    ordered_service_list = sorted(service_list, key=lambda x: x.startup_order)

    env_subst_dict = {
        'execution_id': execution.id,
        'execution_name': execution.name,
        'user_name': execution.owner.username,
        'deployment_name': get_conf().deployment_name,
    }

    for service in execution.services:
        env_subst_dict['dns_name#' + service.name] = service.dns_name

    for service in ordered_service_list:
        env_subst_dict['dns_name#self'] = service.dns_name
        if placement is not None:
            service.assign_backend_host(placement[service.id])
        service.set_starting()
        instance = ServiceInstance(execution, service, env_subst_dict)
        try:
            backend_id, ip_address, ports = backend.spawn_service(instance)
        except ZoeStartExecutionRetryException as ex:
            log.warning('Temporary failure starting service {} of execution {}: {}'.format(service.id, execution.id, ex.message))
            service.set_error(ex.message)
            execution.set_error_message(ex.message)
            terminate_execution(execution)
            execution.set_scheduled()
            return "requeue"
        except ZoeStartExecutionFatalException as ex:
            log.error('Fatal error trying to start service {} of execution {}: {}'.format(service.id, execution.id, ex.message))
            service.set_error(ex.message)
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
            log.debug('Service {} started'.format(instance.name))
            service.set_active(backend_id, ip_address, ports)

    return "ok"


def start_all(execution: Execution) -> str:
    """Translate an execution object into containers.

    If an error occurs some containers may have been created and needs to be cleaned-up.
    """
    log.debug('starting all services for execution {}'.format(execution.id))
    execution.set_starting()
    return service_list_to_containers(execution, execution.services)


def start_essential(execution: Execution, placement) -> str:
    """Start the essential services for this execution"""
    log.debug('starting essential services for execution {}'.format(execution.id))
    execution.set_starting()

    return service_list_to_containers(execution, execution.essential_services, placement)


def start_elastic(execution: Execution, placement) -> str:
    """Start the runnable elastic services"""
    elastic_to_start = [s for s in execution.elastic_services if s.status == Service.RUNNABLE_STATUS]
    return service_list_to_containers(execution, elastic_to_start, placement)


def terminate_service(service: Service) -> None:
    """Terminate a single service."""
    backend = _get_backend()
    if service.status != Service.INACTIVE_STATUS:
        if service.status == Service.ERROR_STATUS:
            backend.terminate_service(service)
            log.debug('Service {} terminated'.format(service.name))
        elif service.status == Service.ACTIVE_STATUS or service.status == Service.TERMINATING_STATUS or service.status == Service.STARTING_STATUS:
            service.set_terminating()
            backend.terminate_service(service)
            service.set_inactive()
            log.debug('Service {} terminated'.format(service.name))
        elif service.status == Service.CREATED_STATUS or service.status == Service.RUNNABLE_STATUS:
            service.set_inactive()
        else:
            log.error('BUG: don\'t know how to terminate a service in status {}'.format(service.status))
    elif not service.is_dead():
        log.warning('Service {} is inactive for Zoe, but running for the back-end, terminating and resetting state'.format(service.name))
        service.set_terminating()
        backend.terminate_service(service)
        service.set_inactive()
        log.debug('Service {} terminated'.format(service.name))


def terminate_execution(execution: Execution) -> None:
    """Terminate an execution."""
    for service in execution.services:  # type: Service
        terminate_service(service)
    execution.set_terminated()


def get_platform_state() -> ClusterStats:
    """Retrieves the state of the platform by querying the container backend. Platform state includes information on free/reserved resources for each node."""
    backend = _get_backend()
    return backend.platform_state()


def preload_image(image_name):
    """Make a service image available on the cluster, according to the backend support."""
    backend = _get_backend()
    log.debug('Preloading image {}'.format(image_name))
    time_start = time.time()
    try:
        backend.preload_image(image_name)
        log.info('Image {} preloaded in {:.2f}s'.format(image_name, time.time() - time_start))
    except NotImplementedError:
        log.warning('Backend {} does not support image preloading'.format(get_conf().backend))


def update_service_resource_limits(service, cores=None, memory=None):
    """Update a service reservation."""
    backend = _get_backend()
    if 'gpu' not in service.labels:  # see https://github.com/NVIDIA/nvidia-docker/issues/515
        backend.update_service(service, cores, memory)


def node_list():
    """List node names configured in the back-end."""
    backend = _get_backend()
    return backend.node_list()


def list_available_images(node_name):
    """List the images available on the specified node."""
    backend = _get_backend()
    return backend.list_available_images(node_name)
