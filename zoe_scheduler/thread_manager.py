from threading import Thread, Event, Semaphore
import logging

log = logging.getLogger(__name__)


class ThreadManager:
    """
    This is for internal tasks of the Zoe scheduler component.
    """
    def __init__(self):
        self.tasks = []
        self.terminate = Event()
        self.terminate.clear()
        self.started = Semaphore(0)

    def add_periodic_task(self, name, func, interval):
        th = Thread(name=name, target=self._generic_task, args=(name, interval, func, self.started))
        th.daemon = True
        self.tasks.append(th)

    def _generic_task(self, name, delay, func, started):
        log.info("Task {} started".format(name))
        init_done = False
        while True:
            try:
                func()
            except:
                log.exception("Task {} raised an exception".format(name))
            if not init_done:
                init_done = True
                started.release()
            stop = self.terminate.wait(delay)
            if stop:
                break
        log.info("Task {} ended".format(name))

    def add_thread(self, name, func):
        th = Thread(name=name, target=func, args=(self.terminate, self.started))
        self.tasks.append(th)

    def start_all(self):
        for th in self.tasks:
            th.start()
            self.started.acquire()

    def stop_all(self):
        self.terminate.set()
        for t in self.tasks:
            t.join()
        log.info("All tasks terminated")
