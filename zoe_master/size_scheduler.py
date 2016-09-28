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

"""The Scheduler."""

import logging
import threading

from zoe_lib.sql_manager import Execution, ComputeNode
from zoe_lib.swarm_client import SwarmClient
from zoe_lib.config import get_conf
from zoe_lib.sql_manager import SQLManager

from zoe_master.exceptions import ZoeStartExecutionFatalException, ZoeStartExecutionRetryException
from zoe_master.zapp_to_docker import execution_to_containers, terminate_execution
from zoe_master.stats import SwarmNodeStats

log = logging.getLogger(__name__)


class SizeBasedJob:
    """An execution with size information."""
    def __init__(self, execution: Execution):
        self.execution = execution
        self.termination_lock = threading.Lock()


class ZoeSizeBasedScheduler:
    """The Scheduler class for size-based scheduling."""
    def __init__(self, state: SQLManager):
        self.trigger_semaphore = threading.Semaphore(0)
        self.queue = []
        self.async_threads = []
        self.loop_quit = False
        self.loop_th = threading.Thread(target=self.loop_start_th, name='scheduler')
        self.loop_th.start()
        self.state = state
        self._update_platform_status()

    def trigger(self):
        """Trigger a scheduler run."""
        self.trigger_semaphore.release()

    def incoming(self, execution: Execution):
        """
        This method adds the execution to the end of the FIFO queue and triggers the scheduler.
        :param execution: The execution
        :return:
        """
        job = SizeBasedJob(execution)
        self.queue.append(job)
        self.trigger()

    def terminate(self, execution: Execution) -> None:
        """
        Inform the master that an execution has been terminated. This can be done asynchronously.
        :param execution: the terminated execution
        :return: None
        """
        def async_termination():
            """Actual termination runs in a thread."""
            with job.termination_lock:
                terminate_execution(execution)
                self.trigger()

        job = None
        for job_aux in self.queue:  # type: SizeBasedJob
            if execution == job_aux.execution:
                job = job_aux
                self.queue.remove(job_aux)
                break

        th = threading.Thread(target=async_termination, name='termination_{}'.format(execution.id))
        th.start()
        self.async_threads.append(th)

    def remove_execution(self, execution: Execution):
        """Removes the execution form the queue."""
        try:
            pass
        except ValueError:
            pass

    def _refresh_job_sizes(self):
        for job in self.queue:
            

    def loop_start_th(self):
        """The Scheduler thread loop."""
        while True:
            ret = self.trigger_semaphore.acquire(timeout=1)
            if not ret:  # Semaphore timeout, do some thread cleanup
                counter = len(self.async_threads)
                while counter > 0:
                    if len(self.async_threads) == 0:
                        break
                    th = self.async_threads.pop(0)
                    th.join(0.1)
                    if th.isAlive():  # join failed
                        log.debug('Thread {} join failed'.format(th.name))
                        self.async_threads.append(th)
                    counter -= 1
                continue
            if self.loop_quit:
                break

            log.debug("Scheduler loop has been triggered")
            self._update_platform_status()

            while True:  # Inner loop will run until no new executions can be started
                self._refresh_job_sizes()

                if len(self.queue) == 0:
                    break

            ##### code to throw away
            e = self.fifo_queue[0]
            assert isinstance(e, Execution)
            e.set_starting()
            self.fifo_queue.pop(0)  # remove the execution form the queue

            try:
                execution_to_containers(e)
            except ZoeStartExecutionRetryException as ex:
                log.warning('Temporary failure starting execution {}: {}'.format(e.id, ex.message))
                e.set_error_message(ex.message)
                terminate_execution(e)
                e.set_scheduled()
                self.fifo_queue.append(e)
            except ZoeStartExecutionFatalException as ex:
                log.error('Fatal error trying to start execution {}: {}'.format(e.id, ex.message))
                e.set_error_message(ex.message)
                terminate_execution(e)
                e.set_error()
            except Exception as ex:
                log.exception('BUG, this error should have been caught earlier')
                e.set_error_message(str(ex))
                terminate_execution(e)
                e.set_error()
            else:
                e.set_running()

    def quit(self):
        """Stop the scheduler thread."""
        self.loop_quit = True
        self.trigger()
        self.loop_th.join()

    def stats(self):
        """Scheduler statistics."""
        return {
            'queue_length': len(self.fifo_queue),
            'termination_threads_count': len(self.async_threads)
        }

    def _update_platform_status(self):
        swarm = SwarmClient(get_conf())
        info = swarm.info()
        for node in info.nodes:  # type: SwarmNodeStats
            node_state = self.state.compute_node_list(only_one=True, id=node.name)
            if node_state is None:
                self.state.compute_node_new(node.name, node.cores_total - node.cores_reserved, node.memory_total - node.memory_reserved, node.labels)
            else:
                self.state.compute_node_update(node.name, free_cores=node.cores_total - node.cores_reserved, reserved_cores=node.cores_reserved, free_memory=node.memory_total - node.memory_reserved, reserved_memory=node.memory_reserved)
