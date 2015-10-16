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

from argparse import ArgumentParser, Namespace
import logging
import sys

from zoe_scheduler.scheduler import ZoeScheduler
from zoe_scheduler.thread_manager import ThreadManager
from zoe_scheduler.ipc import ZoeIPCServer
from zoe_scheduler.platform_manager import PlatformManager
from zoe_scheduler.scheduler_policies import SimpleSchedulerPolicy
from zoe_scheduler.state import create_tables, init as state_init
from common.configuration import conf_init, zoe_conf

log = logging.getLogger(__name__)


def process_arguments_scheduler() -> Namespace:
    argparser = ArgumentParser(description="Zoe Scheduler - Container Analytics as a Service scheduling component")
    argparser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    argparser.add_argument('--setup-db', action='store_true', help='Sets up the configured database for use with the Zoe scheduler')

    return argparser.parse_args()


def zoe_scheduler():
    """
    The entrypoint for the zoe-scheduler script.
    :return: int
    """
    args = process_arguments_scheduler()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('requests').setLevel(logging.WARNING)

    conf_init()

    db_engine = state_init(zoe_conf().db_url)
    if args.setup_db:
        create_tables(db_engine)
        sys.exit(0)

    zoe_sched = ZoeScheduler()
    pm = PlatformManager(zoe_sched)
    zoe_sched.set_policy(SimpleSchedulerPolicy)

    ipc_server = ZoeIPCServer(zoe_sched)

    tm = ThreadManager()
    tm.add_periodic_task("execution health checker", pm.check_executions_health, zoe_conf().check_terminated_interval)
    tm.add_periodic_task("platform status updater", pm.status.update, zoe_conf().status_refresh_interval)
    tm.add_thread("IPC server", ipc_server.ipc_server)

    tm.start_all()

    try:
        zoe_sched.loop()
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt detected, exiting...")

    tm.stop_all()
