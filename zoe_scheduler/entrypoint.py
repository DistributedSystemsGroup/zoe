from argparse import ArgumentParser, Namespace
import logging

from zoe_scheduler.scheduler import ZoeScheduler
from zoe_scheduler.periodic_tasks import PeriodicTaskManager
from zoe_scheduler.ipc import ZoeIPCServer
from zoe_scheduler.object_storage import init_history_paths
from zoe_scheduler.proxy_manager import init as proxy_init
from zoe_scheduler.state import create_tables, init as state_init
from common.configuration import init as conf_init, zoeconf

argparser = None
db_engine = None


def setup_db_cmd(_):
    create_tables(db_engine)


def process_arguments_manage() -> Namespace:
    global argparser
    argparser = ArgumentParser(description="Zoe - Container Analytics as a Service ops client")
    argparser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug output')
    subparser = argparser.add_subparsers(title='subcommands', description='valid subcommands')

    argparser_setup_db = subparser.add_parser('setup-db', help="Create the tables in the database")
    argparser_setup_db.set_defaults(func=setup_db_cmd)

    return argparser.parse_args()


def zoe_manage():
    """
    The entry point for the zoe-manage script.
    :return: int
    """
    global db_engine
    args = process_arguments_manage()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    conf_init()

    db_engine = state_init(zoeconf().db_url)

    try:
        args.func(args)
    except AttributeError:
        argparser.print_help()
        return 1


def process_arguments_scheduler() -> Namespace:
    argparser = ArgumentParser(description="Zoe Scheduler - Container Analytics as a Service scheduling component")
    argparser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    argparser.add_argument('--ipc-server-port', type=int, default=8723, help='Port the IPC server should bind to')

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
    state_init(zoeconf().db_url)
    proxy_init()

    zoe_sched = ZoeScheduler()

    ipc_server = ZoeIPCServer(zoe_sched, args.ipc_server_port)

    if not init_history_paths():
        return

    tm = PeriodicTaskManager()

    barrier = zoe_sched.init_tasks(tm)
    barrier.wait()  # wait for all tasks to be ready and running

    ipc_server.start_thread()

    zoe_sched.loop()

    tm.stop_all()
