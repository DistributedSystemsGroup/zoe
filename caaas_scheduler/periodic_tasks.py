import asyncio


@asyncio.coroutine
def periodic_routine(func, interval):
    while True:
        yield from asyncio.sleep(interval)
        func()


def periodic_task(func, interval) -> asyncio.Task:
    return asyncio.Task(periodic_routine(func, interval))
