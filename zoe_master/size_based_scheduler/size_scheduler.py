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
import time

from zoe_lib.sql_manager import Execution
from zoe_lib.swarm_client import SwarmClient
from zoe_lib.config import get_conf
from zoe_lib.sql_manager import SQLManager

from zoe_master.size_based_scheduler.size_based_job import SizeBasedJob
from zoe_master.size_based_scheduler.simulated_platform import SimulatedPlatform
from zoe_master.zapp_to_docker import terminate_execution
from zoe_master.stats import SwarmNodeStats

log = logging.getLogger(__name__)


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
        def async_termination_job(in_job):
            """Actual termination runs in a thread."""
            with in_job.termination_lock:
                terminate_execution(in_job.execution)
                self.trigger()

        def async_termination_execution(in_execution):
            """Thread for termination when job is not available (leftovers after a master restart)"""
            terminate_execution(in_execution)
            self.trigger()

        job = None
        for job_aux in self.queue:  # type: SizeBasedJob
            if execution == job_aux.execution:
                job = job_aux
                self.queue.remove(job_aux)
                break

        if job is not None:
            th = threading.Thread(target=async_termination_job, name='termination_{}'.format(execution.id), args=(job,))
        else:
            th = threading.Thread(target=async_termination_execution, name='termination_{}'.format(execution.id), args=(execution,))
        th.start()
        self.async_threads.append(th)

    def _cleanup_async_threads(self):
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

    def _refresh_job_sizes(self):
        for job in self.queue:  # type: SizeBasedJob
            if job.last_time_scheduled == 0:
                progress = 0
            else:
                last_progress = (time.time() - job.last_time_scheduled) / ((job.num_services / job.running_services) * job.size_hint)
                job.progress_sequence.append(last_progress)
                progress = sum(job.progress_sequence)
            remaining_execution_time = (1 - progress) * job.size_hint
            job.size = remaining_execution_time * job.num_services

    def _pop_all_with_same_size(self):
        out_list = []
        while len(self.queue) > 0:
            if len(out_list) > 0 and self.queue[0].size != out_list[0].size:
                break
            job = self.queue.pop(0)
            ret = job.termination_lock.acquire(blocking=False)
            if ret and job.execution.status != Execution.TERMINATED_STATUS:
                out_list.append(job)
            else:
                log.debug('While popping, throwing away execution {} that has the termination lock held'.format(job.execution.id))

        return out_list

    def loop_start_th(self):
        """The Scheduler thread loop."""
        while True:
            ret = self.trigger_semaphore.acquire(timeout=1)
            if not ret:  # Semaphore timeout, do some thread cleanup
                self._cleanup_async_threads()
                continue
            if self.loop_quit:
                break

            if len(self.queue) == 0:
                log.debug("Scheduler loop has been triggered, but the queue is empty")
                continue
            log.debug("Scheduler loop has been triggered")

            while True:  # Inner loop will run until no new executions can be started or the queue is empty
                self._refresh_job_sizes()
                self._update_platform_status()

                self.queue.sort()
                log.debug('--> Queue dump after sorting')
                for j in self.queue:
                    log.debug(str(j))
                log.debug('--> End dump')

                jobs_to_attempt_scheduling = self._pop_all_with_same_size()
                log.debug('Scheduler inner loop, jobs to attempt scheduling:')
                for job in jobs_to_attempt_scheduling:
                    log.debug("-> {}".format(job))

                cluster_status_snapshot = SimulatedPlatform(self.state)
                log.debug(str(cluster_status_snapshot))

                jobs_to_launch = []
                free_resources = cluster_status_snapshot.aggregated_free_memory()

                # Try to find a placement solution using a snapshot of the platform status
                for job in jobs_to_attempt_scheduling:  # type: SizeBasedJob
                    # remove all elastic services from the previous simulation loop
                    for job_aux in jobs_to_launch:  # type: SizeBasedJob
                        cluster_status_snapshot.deallocate_elastic(job_aux)

                    job_can_start = False
                    if not job.is_running:
                        job_can_start = cluster_status_snapshot.allocate_essential(job)

                    if job_can_start or job.is_running:
                        jobs_to_launch.append(job)

                    # Try to put back the elastic services
                    for job_aux in jobs_to_launch:
                        cluster_status_snapshot.allocate_elastic(job_aux)

                    current_free_resources = cluster_status_snapshot.aggregated_free_memory()
                    if current_free_resources >= free_resources and len(jobs_to_launch) > 0:
                        job_aux = jobs_to_launch.pop()
                        cluster_status_snapshot.deallocate_essential(job_aux)
                        cluster_status_snapshot.deallocate_elastic(job_aux)
                        for job_aux in jobs_to_launch:
                            cluster_status_snapshot.allocate_elastic(job_aux)
                    free_resources = current_free_resources

                log.debug('Allocation after simulation: {}'.format(cluster_status_snapshot.get_service_allocation()))

                # We port the results of the simulation into the real cluster
                for job in jobs_to_launch:  # type: SizeBasedJob
                    if not job.essentials_started:
                        ret = job.start_essential(cluster_status_snapshot)
                        if ret == "fatal":
                            continue  # trow away the execution
                        elif ret == "requeue":
                            self.queue.append(job)
                            continue
                        assert ret == "ok"

                    job.start_elastic(cluster_status_snapshot)

                    if job.all_services_are_running:
                        log.debug('execution {}: all services started'.format(job.execution.id))
                        job.termination_lock.release()
                        jobs_to_attempt_scheduling.remove(job)

                for job in jobs_to_attempt_scheduling:
                    job.termination_lock.release()
                    self.queue.append(job)

                if len(self.queue) == 0:
                    log.debug('empty queue, exiting inner loop')
                    break
                if len(jobs_to_launch) == 0:
                    log.debug('No executions could be started, exiting inner loop')
                    break

    def quit(self):
        """Stop the scheduler thread."""
        self.loop_quit = True
        self.trigger()
        self.loop_th.join()

    def stats(self):
        """Scheduler statistics."""
        return {
            'queue_length': len(self.queue),
            'termination_threads_count': len(self.async_threads)
        }

    def _update_platform_status(self):
        swarm = SwarmClient(get_conf())
        info = swarm.info()
        for node in info.nodes:  # type: SwarmNodeStats
            node_state = self.state.compute_node_list(only_one=True, id=node.name)
            if node_state is None:
                self.state.compute_node_new(node.name, node.cores_total - node.cores_reserved, node.cores_reserved, node.memory_total - node.memory_reserved, node.memory_reserved, node.container_count, node.labels)
            else:
                self.state.compute_node_update(node.name, free_cores=node.cores_total - node.cores_reserved, reserved_cores=node.cores_reserved, free_memory=node.memory_total - node.memory_reserved, reserved_memory=node.memory_reserved, container_count=node.container_count)
