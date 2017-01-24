"""Classes to hold the system state and simulated container/service placements"""

from zoe_lib.state.sql_manager import Execution, Service
from zoe_master.stats import ClusterStats, NodeStats


class SimulatedNode:
    """A simulated node where containers can be run"""
    def __init__(self, real_node: NodeStats):
        self.real_reservations = {
            "memory": real_node.memory_reserved
        }
        self.real_free_resources = {
            "memory": real_node.memory_free
        }
        self.real_active_containers = real_node.container_count
        self.services = []
        self.name = real_node.name

    def service_fits(self, service: Service) -> bool:
        """Checks whether a service can fit in this node"""
        return service.resource_reservation.memory < self.node_free_memory()

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
        simulated_reservation = 0
        for service in self.services:  # type: Service
            simulated_reservation += service.resource_reservation.memory
        assert (self.real_free_resources['memory'] - simulated_reservation) >= 0
        return self.real_free_resources['memory'] - simulated_reservation

    def __repr__(self):
        out = 'SN {} | f {}'.format(self.name, self.node_free_memory())
        return out


class SimulatedPlatform:
    """A simulated cluster, composed by simulated nodes"""
    def __init__(self, plastform_status: ClusterStats):
        self.nodes = {}
        for node in plastform_status.nodes:
            self.nodes[node.name] = SimulatedNode(node)

    def allocate_essential(self, execution: Execution) -> bool:
        """Try to find an allocation for essential services"""
        for service in execution.essential_services:
            candidate_nodes = []
            for node_id_, node in self.nodes.items():
                if node.service_fits(service):
                    candidate_nodes.append(node)
            if len(candidate_nodes) == 0:  # this service does not fit anywhere
                self.deallocate_essential(execution)
                return False
            candidate_nodes.sort(key=lambda n: n.container_count)  # smallest first
            candidate_nodes[0].service_add(service)
        return True

    def deallocate_essential(self, execution: Execution):
        """Remove all essential services from the simulated cluster"""
        for service in execution.essential_services:
            for node_id_, node in self.nodes.items():
                if node.service_remove(service):
                    break

    def allocate_elastic(self, execution: Execution) -> bool:
        """Try to find an allocation for elastic services"""
        at_least_one_allocated = False
        for service in execution.elastic_services:
            if service.status == service.ACTIVE_STATUS:
                continue
            candidate_nodes = []
            for node_id_, node in self.nodes.items():
                if node.service_fits(service):
                    candidate_nodes.append(node)
            if len(candidate_nodes) == 0:  # this service does not fit anywhere
                continue
            candidate_nodes.sort(key=lambda n: n.container_count)  # smallest first
            candidate_nodes[0].service_add(service)
            service.set_runnable()
            at_least_one_allocated = True
        return at_least_one_allocated

    def deallocate_elastic(self, execution: Execution):
        """Remove all elastic services from the simulated cluster"""
        for service in execution.elastic_services:
            for node_id_, node in self.nodes.items():
                if node.service_remove(service):
                    service.set_inactive()
                    break

    def aggregated_free_memory(self):
        """Return the amount of free memory across all nodes"""
        total = 0
        for node_id_, node in self.nodes.items():
            total += node.node_free_memory()
        return total

    def get_service_allocation(self):
        """Return a map of service IDs to nodes where they have been allocated."""
        placements = {}
        for node_id, node in self.nodes.items():
            for service in node.services:
                placements[service.id] = node_id
        return placements

    def __repr__(self):
        out = ''
        for node_id_, node in self.nodes.items():
            out += str(node) + " # "
        return out
