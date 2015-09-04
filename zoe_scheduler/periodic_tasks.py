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

    def add_task(self, name, func, delay):
        th = Thread(name=name, target=self._generic_task, args=(name, delay, func))
        th.daemon = True
        th.start()

    def _generic_task(self, name, delay, func):
        log.info("Task {} started".format(name))
        while True:
            try:
                func()
            except:
                log.exception("Task {} raised an exception".format(name))
            stop = self.terminate.wait(delay)
            if stop:
                break
        log.info("Task {} ended".format(name))

    def stop_all(self):
        self.terminate.set()
        for t in self.tasks:
            t.join()
        log.info("All tasks terminated")
