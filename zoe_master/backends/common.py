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

from typing import Dict

from zoe_lib.config import get_conf
from zoe_lib.state import Service, Execution
from zoe_master.backends.proxy import gen_proxypath, JUPYTER_NOTEBOOK, MONGO_EXPRESS, JUPYTER_PORT, MONGO_PORT
from zoe_master.exceptions import ZoeStartExecutionFatalException
from zoe_master.workspace.filesystem import ZoeFSWorkspace


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

    # FIXME this code needs to be removed/changed to be generic
    #if 'jupyter' in service.image_name:
    env_list.append((JUPYTER_NOTEBOOK, gen_proxypath(execution, service) + '/' + JUPYTER_PORT))
    #elif 'mongo-express' in service.image_name:
    env_list.append((MONGO_EXPRESS, gen_proxypath(execution, service) + '/' + MONGO_PORT))

    env_list.append(('EXECUTION_ID', str(execution.id)))
    env_list.append(('DEPLOY_NAME', get_conf().deployment_name))
    env_list.append(('UID', execution.user_id))
    env_list.append(('SERVICE_NAME', service.name))
    env_list.append(('PROXY_PATH', get_conf().proxy_path))

    fswk = ZoeFSWorkspace()
    env_list.append(('ZOE_WORKSPACE', fswk.get_mountpoint()))
    return env_list


def gen_volumes(service_: Service, execution: Execution):
    """Return the list of default volumes to be added to all containers."""
    vol_list = []
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
