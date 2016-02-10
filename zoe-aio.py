#!/usr/bin/python3

# Copyright (c) 2016, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import multiprocessing
import time

from zoe_lib.exceptions import ZoeException

log = logging.getLogger('ZoeAIO')


def start_sched():
    from zoe_scheduler.entrypoint import main
    main()


def start_observer():
    from zoe_observer.entrypoint import main
    main()

sched = multiprocessing.Process(target=start_sched, name='scheduler')
obs = multiprocessing.Process(target=start_observer, name='observer')

sched.start()
obs.start()

try:
    while True:
        procs = multiprocessing.active_children()
        if len(procs) == 0:
            raise ZoeException('All Zoe processes crashed, exiting')
        elif len(procs) == 1:
            raise ZoeException('A process crashed, terminating {} that is still alive'.format(procs[0].name))
        else:
            time.sleep(1)
except ZoeException as e:
    log.error(str(e))
except KeyboardInterrupt:
    log.info('CTRL-C detected, exiting...')
finally:
    sched.terminate()
    obs.terminate()
