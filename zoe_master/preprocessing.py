# Copyright (c) 2016, Daniele Venzano
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

"""Layer in front of the scheduler to perform request pre-processing."""

import logging
import os
import shutil

from zoe_lib.state import Execution, SQLManager
from zoe_lib.config import get_conf
from zoe_master.scheduler import ZoeBaseScheduler
from zoe_master.backends.interface import terminate_execution, node_list, list_available_images

log = logging.getLogger(__name__)


def _digest_application_description(state: SQLManager, execution: Execution):
    """Read an application description and expand it into services that can be deployed."""
    nodes = node_list()
    images = []
    for node in nodes:
        images += list_available_images(node)

    images = [name for image in images for name in image['names']]
    for service_descr in execution.description['services']:
        if service_descr['image'] not in images:
            execution.set_error()
            execution.set_error_message('image {} is not available'.format(service_descr['image']))
            return False

    for service_descr in execution.description['services']:
        essential_count = service_descr['essential_count']
        total_count = service_descr['total_count']
        elastic_count = total_count - essential_count
        counter = 0
        for service_n_ in range(essential_count):
            name = "{}{}".format(service_descr['name'], counter)
            sid = state.services.insert(execution.id, name, service_descr['name'], service_descr, True)

            # Ports
            for port_descr in service_descr['ports']:
                port_internal = str(port_descr['port_number']) + '/' + port_descr['protocol']
                state.ports.insert(sid, port_internal, port_descr)

            counter += 1

        for service_n_ in range(elastic_count):
            name = "{}{}".format(service_descr['name'], counter)
            sid = state.services.insert(execution.id, name, service_descr['name'], service_descr, False)

            # Ports
            for port_descr in service_descr['ports']:
                port_internal = str(port_descr['port_number']) + '/' + port_descr['protocol']
                state.ports.insert(sid, port_internal, port_descr)

            counter += 1
        assert counter == total_count

    if get_conf().scheduler_policy == 'DYNSIZE':
        execution.set_size(execution.total_reservations.cores.min * execution.total_reservations.memory.min)

    return True


def execution_submit(state: SQLManager, scheduler: ZoeBaseScheduler, execution: Execution):
    """Submit a new execution to the scheduler."""
    if _digest_application_description(state, execution):
        execution.set_scheduled()
        scheduler.incoming(execution)


def execution_terminate(scheduler: ZoeBaseScheduler, execution: Execution):
    """Remove an execution form the scheduler."""
    if execution.is_running or execution.status == execution.SCHEDULED_STATUS:
        execution.set_cleaning_up()
        scheduler.terminate(execution)
    elif execution.status == execution.SUBMIT_STATUS or execution.status == execution.STARTING_STATUS:
        return  # It is unsafe to terminate executions in these statuses
    elif execution.status == execution.ERROR_STATUS or execution.status == execution.CLEANING_UP_STATUS:
        terminate_execution(execution)
    elif execution.status == execution.TERMINATED_STATUS:
        return


def restart_resubmit_scheduler(state: SQLManager, scheduler: ZoeBaseScheduler):
    """Restart work after a restart of the process."""
    submitted_execs = state.executions.select(status=Execution.SUBMIT_STATUS)
    for e in submitted_execs:
        execution_submit(state, scheduler, e)

    sched_execs = state.executions.select(status=Execution.SCHEDULED_STATUS)
    for e in sched_execs:
        scheduler.incoming(e)

    clean_up_execs = state.executions.select(status=Execution.CLEANING_UP_STATUS)
    for e in clean_up_execs:
        scheduler.terminate(e)

    starting_execs = state.executions.select(status=Execution.STARTING_STATUS)
    for e in starting_execs:
        scheduler.terminate(e)
        scheduler.incoming(e)


def execution_delete(execution: Execution):
    """Remove an execution, must only be called if the execution is NOT running."""
    assert not execution.is_active
    path = os.path.join(get_conf().service_logs_base_path, get_conf().deployment_name, str(execution.id))
    if path is None:
        return

    shutil.rmtree(path, ignore_errors=True)
