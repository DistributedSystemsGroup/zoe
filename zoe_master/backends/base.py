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
        """Initializes Swarm backend starting the event monitoring thread."""
        raise NotImplementedError

    def shutdown(self):
        """Performs a clean shutdown of the resources used by Swarm backend."""
        raise NotImplementedError

    def spawn_service(self, execution: Execution, service: Service, env_subst_dict: Dict):
        """Create a container for a service."""
        raise NotImplementedError

    def terminate_service(self, service: Service) -> None:
        """Terminate the container corresponding to a service."""
        raise NotImplementedError

    def platform_state(self) -> ClusterStats:
        """Get the platform state."""
        raise NotImplementedError
