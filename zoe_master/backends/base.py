# Copyright (c) 2017, Daniele Venzano
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

"""The base class that all backends should implement."""

from typing import Dict

from zoe_lib.state import Execution, Service
from zoe_master.stats import ClusterStats


class BaseBackend:
    """The base class that all backends should implement."""
    def __init__(self, conf):
        pass

    def init(self, state):
        """Initializes the backend. In general this includes finding the current API endpoint and opening a connection to it, negotiate the API version, etc. Here backend-related threads can be started, too. This method will be called only once at Zoe startup."""
        raise NotImplementedError

    def shutdown(self):
        """Performs a clean shutdown of the resources used by Swarm backend. Any threads that where started in the init() method should be terminated here. This method will be called when Zoe shuts down."""
        raise NotImplementedError

    def spawn_service(self, execution: Execution, service: Service, env_subst_dict: Dict):
        """Create a container for a service."""
        raise NotImplementedError

    def terminate_service(self, service: Service) -> None:
        """Terminate the container corresponding to a service."""
        raise NotImplementedError

    def platform_state(self) -> ClusterStats:
        """Get the platform state. This method should fill-in a new ClusterStats object at each call, with fresh statistics on the available nodes and resource availability. This information will be used for taking scheduling decisions."""
        raise NotImplementedError
