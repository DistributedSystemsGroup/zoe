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

from typing import Dict, List

from zoe_lib.config import get_conf
from zoe_lib.state import Service, Execution, VolumeDescription
from zoe_lib.workspace.filesystem import ZoeFSWorkspace
from zoe_master.exceptions import ZoeStartExecutionFatalException


def gen_environment(execution: Execution, service: Service, env_subst_dict: Dict):
    """ Generate a dictionary containing the current cluster status (before the new container is spawned)

    This information is used to substitute template strings in the environment variables."""
    env_list = []
    for env_name, env_value in service.environment:
        try:
            env_value = env_value.format(**env_subst_dict)
        except KeyError:
            error_msg = "Unknown variable in environment expression '{}', known variables are: {}".format(env_value, list(env_subst_dict.keys()))
            service.set_error(error_msg)
            raise ZoeStartExecutionFatalException("Service {} has wrong environment expression")
        env_list.append((env_name, env_value))

    env_list.append(('EXECUTION_ID', str(execution.id)))
    env_list.append(('DEPLOY_NAME', get_conf().deployment_name))
    env_list.append(('UID', execution.user_id))
    env_list.append(('SERVICE_NAME', service.name))
    env_list.append(('PROXY_PATH', get_conf().proxy_path))

    wk_vol = ZoeFSWorkspace().get(execution.user_id)
    env_list.append(('ZOE_WORKSPACE', wk_vol.mount_point))
    return env_list


def gen_volumes(service: Service, execution: Execution) -> List[VolumeDescription]:
    """Return the list of default volumes to be added to all containers."""
    vol_list = service.volumes

    fswk = ZoeFSWorkspace()
    wk_vol = fswk.get(execution.user_id)

    vol_list.append(wk_vol)

    return vol_list


def gen_labels(service: Service, execution: Execution):
    """Generate container labels, useful for identifying containers in monitoring systems."""
    return {
        'zoe_execution_name': execution.name,
        'zoe_execution_id': str(execution.id),
        'zoe_service_name': service.name,
        'zoe_service_id': str(service.id),
        'zoe_owner': execution.user_id,
        'zoe_deployment_name': get_conf().deployment_name,
        'zoe_type': 'app_service'
    }
