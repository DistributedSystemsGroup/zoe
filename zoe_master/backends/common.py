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

import os
import logging

from zoe_lib.state import Service, Execution, VolumeDescription
from zoe_lib.config import get_conf
from zoe_master.workspace.filesystem import ZoeFSWorkspace

log = logging.getLogger(__name__)


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


def _create_logs_directories(exec_id, service_name):
    path = os.path.join(get_conf().logs_base_path, get_conf().deployment_name, str(exec_id), service_name)
    try:
        os.makedirs(path)
    except OSError as e:
        log.error('Cannot create path {}: {}'.format(path, str(e)))
        return None
    return path


def gen_volumes(service: Service, execution: Execution):
    """Return the list of default volumes to be added to all containers."""
    vol_list = []
    fswk = ZoeFSWorkspace()
    wk_vol = fswk.get(execution.user_id)

    vol_list.append(wk_vol)

    logs_path = _create_logs_directories(execution.id, service.name)
    if logs_path is not None:
        logs_mountpoint = '/logs'
        logs_vol = VolumeDescription((logs_path, logs_mountpoint, True))
        vol_list.append(logs_vol)

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
