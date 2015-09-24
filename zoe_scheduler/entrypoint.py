from argparse import ArgumentParser, Namespace
import logging
import sys

from zoe_scheduler.scheduler import ZoeScheduler
from zoe_scheduler.thread_manager import ThreadManager
from zoe_scheduler.ipc import ZoeIPCServer
import zoe_scheduler.object_storage as object_storage
from zoe_scheduler.platform_manager import PlatformManager
from zoe_scheduler.scheduler_policies import SimpleSchedulerPolicy
from zoe_scheduler.state import create_tables, init as state_init
from zoe_scheduler.configuration import init as conf_init, scheduler_conf

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

    db_engine = state_init(scheduler_conf().db_url)
    if args.setup_db:
        create_tables(db_engine)
        sys.exit(0)

    zoe_sched = ZoeScheduler()
    pm = PlatformManager(zoe_sched)
    zoe_sched.set_policy(SimpleSchedulerPolicy)

    ipc_server = ZoeIPCServer(zoe_sched)

    if not object_storage.init_history_paths():
        return

    tm = ThreadManager()
    tm.add_thread("Object server", object_storage.object_server)
    tm.add_periodic_task("execution health checker", pm.check_executions_health, scheduler_conf().check_terminated_interval)
    tm.add_periodic_task("platform status updater", pm.status.update, scheduler_conf().status_refresh_interval)
    tm.add_thread("IPC server", ipc_server.ipc_server)

    tm.start_all()

    try:
        zoe_sched.loop()
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt detected, exiting...")

    tm.stop_all()
