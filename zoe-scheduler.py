#!/usr/bin/env python3

import argparse
import asyncio
import logging
log = logging.getLogger('zoe')
import signal

from zoe_scheduler.rpyc_service import ZoeSchedulerRPCService
from zoe_scheduler.rpyc_server import RPyCAsyncIOServer
from zoe_scheduler.scheduler import zoe_sched

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

    return argparser.parse_args()


def main():
    global loop, rpyc_server
    args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('asyncio').setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('asyncio').setLevel(logging.WARNING)

    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('rpyc').setLevel(logging.WARNING)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, sigint_handler)
    rpyc_server = RPyCAsyncIOServer(ZoeSchedulerRPCService, '0.0.0.0', port=4000, auto_register=True)
    rpyc_server.start()

    zoe_sched.init_tasks()

    loop.run_forever()

    loop.close()

if __name__ == "__main__":
    main()
