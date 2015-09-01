#!/usr/bin/env python3

import asyncio
import logging
import signal

from zoe_scheduler.rpyc_service import ZoeSchedulerRPCService
from zoe_scheduler.rpyc_server import RPyCAsyncIOServer
from zoe_scheduler.scheduler import zoe_sched


def sigint_handler():
    log.warning('CTRL-C detected, terminating event loop...')
    loop.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.INFO)
    logging.getLogger('rpyc').setLevel(logging.WARNING)
    log = logging.getLogger('zoe')

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, sigint_handler)
    rpyc_server = RPyCAsyncIOServer(ZoeSchedulerRPCService, '0.0.0.0', port=4000, auto_register=True)
    rpyc_server.start()

    zoe_sched.init_tasks()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log.warning('CTRL-C detected, terminating event loop...')

    loop.run_until_complete(rpyc_server.server.wait_closed())
    loop.close()
