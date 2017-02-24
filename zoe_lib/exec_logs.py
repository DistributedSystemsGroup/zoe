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

"""Container log storage"""

import logging
import os
import shutil

from zoe_lib.state import Execution
from zoe_lib.swarm_client import SwarmClient
from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


def _path_from_execution(execution: Execution):
    return os.path.join(get_conf().service_log_path, get_conf().deployment_name, str(execution.id))


def _init(execution: Execution):
    if get_conf().service_log_path == '':
        return None
    base_path = _path_from_execution(execution)
    try:
        os.makedirs(base_path, exist_ok=True)
    except (OSError, PermissionError):
        log.exception('Error creating the directory at path: {}'.format(base_path))
        return None

    return base_path


def _shutdown():
    pass


def save(execution: Execution):
    """Save the logs of the service specified as argument"""
    path = _init(execution)
    if path is None:
        return

    for service in execution.services:
        fname = service.name + '.txt'
        fpath = os.path.join(path, fname)

        swarm = SwarmClient(get_conf())
        log_gen = swarm.logs(service.docker_id, stream=True, follow=False)
        if log_gen is None:
            _shutdown()
            return
        try:
            with open(fpath, 'wb') as out_fp:
                for line in log_gen:
                    out_fp.write(line)
        except FileNotFoundError:
            log.error("Could not create file {}".format(fpath))

    _shutdown()


def delete(execution: Execution):
    """Delete the logs for a service"""
    path = _init(execution)
    if path is None:
        return

    shutil.rmtree(path, ignore_errors=True)

    _shutdown()
