#!/usr/bin/env python3

import argparse
import logging

from rpyc.utils.server import ThreadedServer

from zoe_scheduler.rpyc_service import ZoeSchedulerRPCService
from zoe_scheduler.scheduler import zoe_sched
from zoe_scheduler.periodic_tasks import PeriodicTaskManager
from zoe_scheduler.ipc import ZoeIPCServer
from common.object_storage import init_history_paths

log = logging.getLogger('zoe')
loop = None
rpyc_server = None


def sigint_handler():
    log.warning('CTRL-C detected, terminating event loop...')
    loop.stop()
    zoe_sched.stop_tasks()
    rpyc_server.stop()
    try:
        loop.run_forever()
    except RuntimeError:
        pass


def process_arguments() -> argparse.Namespace:
    argparser = argparse.ArgumentParser(description="Zoe Scheduler - Container Analytics as a Service scheduling component")
    argparser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    argparser.add_argument('--rpyc-no-auto-register', action='store_true', help='Do not register automatically in the RPyC registry')
    argparser.add_argument('--ipc-server-port', type=int, default=8723, help='Port the IPC server should bind to')

    return argparser.parse_args()


def main():
    global loop, rpyc_server
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('requests').setLevel(logging.WARNING)
    rpyc_logger = logging.getLogger('rpyc')
    rpyc_logger.setLevel(logging.WARNING)

    ipc_server = ZoeIPCServer(zoe_sched, args.ipc_server_port)

    if not init_history_paths():
        return

    tm = PeriodicTaskManager()

    rpyc_server = ThreadedServer(ZoeSchedulerRPCService, '0.0.0.0', port=4000,
                                 auto_register=not args.rpyc_no_auto_register,
                                 protocol_config={"allow_public_attrs": True},
                                 logger=rpyc_logger)

    zoe_sched.init_tasks(tm)

    ipc_server.start_loop()

    rpyc_server.start()

    tm.stop_all()

if __name__ == "__main__":
    main()
