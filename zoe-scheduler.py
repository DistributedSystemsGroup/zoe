#!/usr/bin/env python3

import argparse
import logging

from zoe_scheduler.scheduler import ZoeScheduler
from zoe_scheduler.periodic_tasks import PeriodicTaskManager
from zoe_scheduler.ipc import ZoeIPCServer
from zoe_scheduler.object_storage import init_history_paths
from zoe_scheduler.state import init as state_init

from common.configuration import zoeconf

log = logging.getLogger('zoe')


def process_arguments() -> argparse.Namespace:
    argparser = argparse.ArgumentParser(description="Zoe Scheduler - Container Analytics as a Service scheduling component")
    argparser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    argparser.add_argument('--ipc-server-port', type=int, default=8723, help='Port the IPC server should bind to')

    return argparser.parse_args()


def main():
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('requests').setLevel(logging.WARNING)

    state_init(zoeconf.db_url)

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

if __name__ == "__main__":
    main()
