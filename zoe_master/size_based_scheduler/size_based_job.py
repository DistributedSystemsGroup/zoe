"""A SizeBasedJob is a wrapper around the standard Zoe Execution class that adds size-based information"""

import logging
import threading
from typing import List

from zoe_lib.sql_manager import Execution, Service
from zoe_master.exceptions import ZoeStartExecutionFatalException, ZoeStartExecutionRetryException
from zoe_master.zapp_to_docker import service_list_to_containers, terminate_execution

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
        for service_type in self.execution.description['services']:
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
            if s.service_group in essential_services_counts:
                self.essential_services.append(s)
                essential_services_counts[s.service_group] -= 1
                if essential_services_counts[s.service_group] == 0:
                    del essential_services_counts[s.service_group]
            elif s.service_group in elastic_services_counts:
                self.elastic_services.append(s)
                elastic_services_counts[s.service_group] -= 1
                if elastic_services_counts[s.service_group] == 0:
                    del elastic_services_counts[s.service_group]
            else:
                log.error('service {} is not elastic, nor essential, something is wrong'.format(s.name))

        self.essentials_started = False

    @property
    def is_running(self):
        """Wraps the execution method with the same name"""
        return self.execution.is_running()

    def start_essential(self, simulated_placement):
        """Start the essential services for this execution"""
        allocations = simulated_placement.get_service_allocation()

        log.debug('starting essential services for execution {}'.format(self.execution.id))
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
            log.debug('starting elastic service {} for execution {}'.format(service.id, self.execution.id))
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

    def __repr__(self):
        essential_str = ','.join([str(x.id) for x in self.essential_services])
        elastic_str = ','.join([str(x.id) for x in self.elastic_services])
        s = 'exec {} | essential {} | elastic {} | size hint {} | size {}'.format(self.execution.id, essential_str, elastic_str, self.size_hint, self.size)
        return s
