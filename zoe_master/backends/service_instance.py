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

"""When a service from the application description needs to be instantiated, it is transformed into a ServiceInstance, an internal representation of a generic container. This class is used to gather all the attributes that describe a container and to provide a clear interface with the backend."""

from zoe_lib.state import Service, Execution
from zoe_lib.config import get_conf
import zoe_master.backends.common


class ServiceInstance:
    """The ServiceInstance class, a Service that is going to be instantiated into a container."""
    def __init__(self, execution: Execution, service: Service, env_subst_dict):
        self.name = service.unique_name
        self.hostname = service.dns_name

        self.memory_limit = service.resource_reservation.memory
        self.core_limit = service.resource_reservation.cores

        self.labels = {
            'zoe.execution.name': execution.name,
            'zoe.execution.id': str(execution.id),
            'zoe.service.name': service.name,
            'zoe.service.id': str(service.id),
            'zoe.owner': execution.user_id,
            'zoe.deployment_name': get_conf().deployment_name,
            'zoe.type': 'app_service'
        }
        if service.is_monitor:
            self.labels['zoe_monitor'] = 'true'
        else:
            self.labels['zoe_monitor'] = 'false'

        self.labels = zoe_master.backends.common.gen_labels(service, execution)
        self.environment = service.environment + zoe_master.backends.common.gen_environment(execution, service, env_subst_dict)
        self.volumes = service.volumes + zoe_master.backends.common.gen_volumes(service, execution)

        self.command = service.command

        self.image_name = service.image_name

        self.ports = service.ports

        self.replicas_count = service.replicas
