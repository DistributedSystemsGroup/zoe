import asyncio
import logging
import signal

from caaas_scheduler.rpyc_service import CAaaSSchedulerRPCService
from caaas_scheduler.rpyc_server import RPyCAsyncIOServer
from caaas_scheduler.scheduler import caaas_sched


def sigint_handler():
    log.warning('CTRL-C detected, terminating event loop...')
    loop.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.INFO)
    log = logging.getLogger('caaas')

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, sigint_handler)
    rpyc_server = RPyCAsyncIOServer(CAaaSSchedulerRPCService, '0.0.0.0', port=4000, auto_register=True)
    rpyc_server.start()

    caaas_sched.init_tasks()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log.warning('CTRL-C detected, terminating event loop...')

    loop.run_until_complete(rpyc_server.server.wait_closed())
    loop.close()
