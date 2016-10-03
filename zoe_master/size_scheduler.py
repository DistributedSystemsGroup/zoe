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
from typing import List

from zoe_lib.sql_manager import Execution, ComputeNode
from zoe_lib.swarm_client import SwarmClient
from zoe_lib.config import get_conf
from zoe_lib.sql_manager import SQLManager, Service

from zoe_master.exceptions import ZoeStartExecutionFatalException, ZoeStartExecutionRetryException
from zoe_master.zapp_to_docker import service_list_to_containers, terminate_execution
from zoe_master.stats import SwarmNodeStats

log = logging.getLogger(__name__)


class SizeBasedJob:
    """An execution with size information."""
    def __init__(self, execution: Execution):
        self.execution = execution
        self.termination_lock = threading.Lock()

        self.size_hint = int(execution.description['priority'])
        self.num_services = len(execution.services)
        self.running_services = 0
        self.size = 0

        self.last_time_scheduled = 0
        self.progress_sequence = []

        self.total_reservations = {
            'memory': 0
        }
        for service in self.execution.services:
            self.total_reservations['memory'] += service.description['required_resources']['memory']

        essential_services_counts = {}
        elastic_services_counts = {}
        for service_type in self.execution.description['description']:
            essential_count = service_type['essential_count']
            total_count = service_type['total_count']
            elastic_count = total_count - essential_count
            if essential_count > 0:
                essential_services_counts[service_type['name']] = essential_count
            if elastic_count > 0:
                elastic_services_counts[service_type['name']] = elastic_count

        self.essential_services = []  # type: List[Service]
        self.elastic_services = []  # type: List[Service]
        for s in self.execution.services:
            if s.service_type in essential_services_counts:
                self.essential_services.append(s)
                essential_services_counts[s.service_type] -= 1
                if essential_services_counts[s.service_type] == 0:
                    del essential_services_counts[s.service_type]
            elif s.service_type in elastic_services_counts:
                self.elastic_services.append(s)
                elastic_services_counts[s.service_type] -= 1
                if elastic_services_counts[s.service_type] == 0:
                    del elastic_services_counts[s.service_type]
            else:
                log.error('service {} is not elastic, nor essential, something is wrong'.format(s.name))

        self.essentials_started = False

    @property
    def is_running(self):
        """Wraps the execution method with the same name"""
        return self.execution.is_running()

    def start_essential(self, simulated_placement: SimulatedPlatform):
        """Start the essential services for this execution"""
        allocations = simulated_placement.get_service_allocation()

        self.execution.set_starting()

        try:
            service_list_to_containers(self.execution, self.essential_services, allocations)
        except ZoeStartExecutionRetryException as ex:
            log.warning('Temporary failure starting execution {}: {}'.format(self.execution.id, ex.message))
            self.execution.set_error_message(ex.message)
            terminate_execution(self.execution)
            self.execution.set_scheduled()
            return "requeue"
        except ZoeStartExecutionFatalException as ex:
            log.error('Fatal error trying to start execution {}: {}'.format(self.execution.id, ex.message))
            self.execution.set_error_message(ex.message)
            terminate_execution(self.execution)
            self.execution.set_error()
            return "fatal"
        except Exception as ex:
            log.exception('BUG, this error should have been caught earlier')
            self.execution.set_error_message(str(ex))
            terminate_execution(self.execution)
            self.execution.set_error()
            return "fatal"
        else:
            self.execution.set_running()
            self.essentials_started = True
            return "ok"


    def start_elastic(self, simulated_placement):
        """Start the runnable elastic services"""
        allocations = simulated_placement.get_service_allocation()

        elastic_to_start = [s for s in self.elastic_services if s.status == Service.RUNNABLE_STATUS]

        for service in elastic_to_start:
            try:
                service_list_to_containers(self.execution, [service], allocations)
            except ZoeStartExecutionRetryException as ex:
                log.warning('Temporary failure starting elastic service {}: {}'.format(service.name, ex.message))
                service.set_inactive()
            except ZoeStartExecutionFatalException as ex:
                log.error('Fatal error trying to start elastic service {}: {}'.format(service.name, ex.message))
                service.set_error(ex.message)
            except Exception as ex:
                log.exception('BUG, this error should have been caught earlier')
                service.set_error(str(ex))

    @property
    def all_services_are_running(self):
        """Return True if all services of this execution are running/active"""
        for service in self.execution.services:
            if service.status != service.ACTIVE_STATUS:
                return False
        return True

    def __lt__(self, other):
        """Compare two jobs according to their size and resource requirements."""
        if not isinstance(other, SizeBasedJob):
            return NotImplemented

        if self.size < other.size:
            return True
        elif self.size == other.size:
            if self.total_reservations['memory'] < other.total_reservations['memory']:
                return True
        return False


class SimulatedNode:
    """A simulated node where containers can be run"""
    def __init__(self, real_node: ComputeNode):
        self.real_reservations = {
            "memory": real_node.reserved_memory
        }
        self.real_free_resources = {
            "memory": real_node.free_memory
        }
        self.real_active_containers = real_node.container_count
        self.services = []

    def service_fits(self, service) -> bool:
        """Checks whether a service can fit in this node"""
        if service.description['required_resources']['memory'] < self.node_free_memory():
            return True
        else:
            return False

    def service_add(self, service):
        """Add a service in this node."""
        if self.service_fits(service):
            self.services.append(service)
            return True
        else:
            return False

    def service_remove(self, service):
        """Add a service in this node."""
        try:
            self.services.remove(service)
        except ValueError:
            return False
        else:
            return True

    @property
    def container_count(self):
        """Return the number of containers on this node"""
        return self.real_active_containers + len(self.services)

    def node_free_memory(self):
        """Return the amount of free memory for this node"""
        total_reserved_memory = self.real_reservations['memory']
        for service in self.services:
            total_reserved_memory += service.description['required_resources']['memory']
        return self.real_free_resources['memory'] - total_reserved_memory


class SimulatedPlatform:
    """A simulated cluster, composed by simulated nodes"""
    def __init__(self, state: SQLManager):
        real_nodes = state.compute_node_list()
        self.nodes = {}
        for node in real_nodes:
            self.nodes[node['id']] = SimulatedNode(node)

    def allocate_essential(self, job: SizeBasedJob) -> bool:
        """Try to find an allocation for essential services"""
        for service in job.essential_services:
            candidate_nodes = []
            for node_name, node in self.nodes.items():
                if node.service_fits(service):
                    candidate_nodes.append(node)
            if len(candidate_nodes) == 0:  # this service does not fit anywhere
                self.deallocate_essential(job)
                return False
            candidate_nodes.sort(key=lambda n: n.container_count)  # smallest first
            candidate_nodes[0].service_add(service)
        return True

    def deallocate_essential(self, job: SizeBasedJob):
        """Remove all essential services from the simulated cluster"""
        for service in job.essential_services:
            for node_name, node in self.nodes.items():
                if node.service_remove(service):
                    break

    def allocate_elastic(self, job: SizeBasedJob) -> bool:
        """Try to find an allocation for elastic services"""
        at_least_one_allocated = False
        for service in job.elastic_services:
            if service.status == service.ACTIVE_STATUS:
                continue
            candidate_nodes = []
            for node_name, node in self.nodes.items():
                if node.service_fits(service):
                    candidate_nodes.append(node)
            if len(candidate_nodes) == 0:  # this service does not fit anywhere
                continue
            candidate_nodes.sort(key=lambda n: n.container_count)  # smallest first
            candidate_nodes[0].service_add(service)
            service.set_runnable()
            at_least_one_allocated = True
        return at_least_one_allocated

    def deallocate_elastic(self, job: SizeBasedJob):
        """Remove all elastic services from the simulated cluster"""
        for service in job.essential_services:
            for node_name, node in self.nodes.items():
                if node.service_remove(service):
                    service.set_inactive()
                    break

    def aggregated_free_memory(self):
        """Return the amount of free memory across all nodes"""
        total = 0
        for n in self.nodes:
            total += n.node_free_memory()
        return total

    def get_service_allocation(self):
        """Return a map of service IDs to nodes where they have been allocated."""
        placements = {}
        for node_id, node in self.nodes.items():
            for service in node.services:
                placements[service.id] = node_id
        return placements


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
            remaining_execution_time = (1 - progress) * ((job.num_services / job.running_services) * job.size_hint)
            job.size = remaining_execution_time * job.num_services

    def _pop_all_with_same_size(self):
        out_list = []
        while len(self.queue) > 0:
            if len(out_list) > 0 and self.queue[0].size != out_list[0].size:
                break
            job = self.queue.pop(0)
            ret = job.termination_lock.acquire(blocking=False)
            if ret:
                out_list.append(ret)
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

            log.debug("Scheduler loop has been triggered")
            self._update_platform_status()

            if len(self.queue) == 0:
                continue

            while True:  # Inner loop will run until no new executions can be started or the queue is empty
                self._refresh_job_sizes()

                self.queue.sort()

                jobs_to_attempt_scheduling = self._pop_all_with_same_size()

                cluster_status_snapshot = SimulatedPlatform(self.state)

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
                        jobs_to_attempt_scheduling.remove(job)

                for job in jobs_to_attempt_scheduling:
                    self.queue.append(job)

                if len(self.queue) == 0 or len(jobs_to_launch) == 0:
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
                self.state.compute_node_new(node.name, node.cores_total - node.cores_reserved, node.memory_total - node.memory_reserved, node.labels, node.container_count)
            else:
                self.state.compute_node_update(node.name, free_cores=node.cores_total - node.cores_reserved, reserved_cores=node.cores_reserved, free_memory=node.memory_total - node.memory_reserved, reserved_memory=node.memory_reserved, container_count=node.container_count)
