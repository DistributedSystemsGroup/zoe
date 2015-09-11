from threading import Thread, Event
import logging

log = logging.getLogger(__name__)


class PeriodicTaskManager:
    """
    This is for internal tasks of the Zoe scheduler component, do not confuse this for the application scheduler.
    """
    def __init__(self):
        self.tasks = []
        self.terminate = Event()
        self.terminate.clear()

    def add_task(self, name, func, delay, ready_barrier):
        th = Thread(name=name, target=self._generic_task, args=(name, delay, func, ready_barrier))
        th.daemon = True
        th.start()

    def _generic_task(self, name, delay, func, ready_barrier):
        log.info("Task {} started".format(name))
        init_done = False
        while True:
            try:
                func()
            except:
                log.exception("Task {} raised an exception".format(name))
            if not init_done:
                init_done = True
                ready_barrier.wait()
            stop = self.terminate.wait(delay)
            if stop:
                break
        log.info("Task {} ended".format(name))

    def stop_all(self):
        self.terminate.set()
        for t in self.tasks:
            t.join()
        log.info("All tasks terminated")
