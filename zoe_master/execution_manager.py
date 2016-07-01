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

import logging

import zoe_lib.config as config
from zoe_lib.sql_manager import Execution
from zoe_master.scheduler import ZoeScheduler

log = logging.getLogger(__name__)


def _digest_application_description(execution: Execution):
    for service_descr in execution.description['services']:
        for counter in range(service_descr['total_count']):
            name = "{}{}".format(service_descr['name'], counter)
            config.singletons['sql_manager'].service_new(execution.id, name, service_descr['name'], service_descr)


def execution_submit(execution: Execution):
    assert isinstance(config.scheduler, ZoeScheduler)
    _digest_application_description(execution)
    config.scheduler.incoming(execution)


def execution_terminate(execution: Execution):
    assert isinstance(config.scheduler, ZoeScheduler)
    config.scheduler.terminate(execution)


def restart_resubmit_scheduler():
    assert isinstance(config.scheduler, ZoeScheduler)
    sched_execs = config.singletons['sql_manager'].execution_list(status=Execution.SCHEDULED_STATUS)
    for e in sched_execs:
        config.scheduler.incoming(e)

    clean_up_execs = config.singletons['sql_manager'].execution_list(status=Execution.CLEANING_UP_STATUS)
    for e in clean_up_execs:
        config.scheduler.terminate(e)

    starting_execs = config.singletons['sql_manager'].execution_list(status=Execution.STARTING_STATUS)
    for e in starting_execs:
        config.scheduler.terminate(e)
        config.scheduler.incoming(e)


def execution_delete(execution: Execution):
    assert isinstance(config.scheduler, ZoeScheduler)
    config.scheduler.remove_execution(execution)
