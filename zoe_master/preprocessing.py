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

from zoe_lib.state import Execution, SQLManager
from zoe_master.scheduler import ZoeBaseScheduler

log = logging.getLogger(__name__)


def _digest_application_description(state: SQLManager, execution: Execution):
    """Read an application description and expand it into services that can be deployed."""
    for service_descr in execution.description['services']:
        essential_count = service_descr['essential_count']
        total_count = service_descr['total_count']
        elastic_count = total_count - essential_count
        counter = 0
        for service_n_ in range(essential_count):
            name = "{}{}".format(service_descr['name'], counter)
            state.service_new(execution.id, name, service_descr['name'], service_descr, True)
            counter += 1
        for service_n_ in range(elastic_count):
            name = "{}{}".format(service_descr['name'], counter)
            state.service_new(execution.id, name, service_descr['name'], service_descr, False)
            counter += 1
        assert counter == total_count


def execution_submit(state: SQLManager, scheduler: ZoeBaseScheduler, execution: Execution):
    """Submit a new execution to the scheduler."""
    _digest_application_description(state, execution)
    scheduler.incoming(execution)


def execution_terminate(scheduler: ZoeBaseScheduler, execution: Execution):
    """Remove an execution form the scheduler."""
    scheduler.terminate(execution)


def restart_resubmit_scheduler(state: SQLManager, scheduler: ZoeBaseScheduler):
    """Restart work after a restart of the process."""
    sched_execs = state.execution_list(status=Execution.SCHEDULED_STATUS)
    for e in sched_execs:
        scheduler.incoming(e)

    clean_up_execs = state.execution_list(status=Execution.CLEANING_UP_STATUS)
    for e in clean_up_execs:
        scheduler.terminate(e)

    starting_execs = state.execution_list(status=Execution.STARTING_STATUS)
    for e in starting_execs:
        scheduler.terminate(e)
        scheduler.incoming(e)


def execution_delete(execution: Execution):
    """Remove an execution, must only be called if the execution is NOT running."""
    assert not execution.is_active
