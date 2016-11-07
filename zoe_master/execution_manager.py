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

"""Layer in front of the scheduler to perform """

import logging

from zoe_lib.sql_manager import Execution, SQLManager
from zoe_lib import exec_logs

from zoe_master.scheduler import ZoeScheduler

log = logging.getLogger(__name__)


def _digest_application_description(state: SQLManager, execution: Execution):
    for service_descr in execution.description['services']:
        for counter in range(service_descr['total_count']):
            name = "{}{}".format(service_descr['name'], counter)
            state.service_new(execution.id, name, service_descr['name'], service_descr)


def execution_submit(state: SQLManager, scheduler: ZoeScheduler, execution: Execution):
    """Submit a new execution to the scheduler."""
    _digest_application_description(state, execution)
    scheduler.incoming(execution)


def execution_terminate(scheduler: ZoeScheduler, execution: Execution):
    """Remove an execution form the scheduler."""
    scheduler.terminate(execution)


def restart_resubmit_scheduler(state: SQLManager, scheduler: ZoeScheduler):
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


def execution_delete(scheduler: ZoeScheduler, execution: Execution):
    """Remove an execution from the scheduler."""
    if execution.is_active():
        scheduler.terminate(execution)
    exec_logs.delete(execution)
