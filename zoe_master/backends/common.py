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

"""The high-level interface that Zoe uses to talk to the configured container backend."""

from zoe_lib.state import Service, Execution
from zoe_lib.config import get_conf
from zoe_master.workspace.filesystem import ZoeFSWorkspace


def gen_environment(service: Service, execution: Execution):
    """Return the list of environment variables that needs to be added to all containers."""
    fswk = ZoeFSWorkspace()
    env_list = [
        ('ZOE_EXECUTION_ID', execution.id),
        ('ZOE_EXECUTION_NAME', execution.name),
        ('ZOE_SERVICE_GROUP', service.service_group),
        ('ZOE_SERVICE_NAME', service.name),
        ('ZOE_SERVICE_ID', service.id),
        ('ZOE_OWNER', execution.user_id),
        ('ZOE_DEPLOYMENT_NAME', get_conf().deployment_name),
        ('ZOE_MY_DNS_NAME', service.dns_name),
        ('ZOE_WORKSPACE', fswk.get_mountpoint())
    ]
    service_list = []
    for tmp_service in execution.services:
        service_list.append(tmp_service.dns_name)
    env_list.append(('ZOE_EXECUTION_SERVICE_LIST', ','.join(service_list)))

    return env_list


def gen_volumes(service: Service, execution: Execution):
    """Return the list of default volumes to be added to all containers."""
    vol_list = []
    fswk = ZoeFSWorkspace()
    if fswk.can_be_attached():
        vol_list.append(fswk.get(execution.user_id))

    return vol_list
