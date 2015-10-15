# Copyright (c) 2015, Daniele Venzano
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

"""
This module contains all diagnostics-related API calls for Zoe clients.
"""

from zoe_client.lib.ipc import ZoeIPCClient
from zoe_client.scheduler_classes.execution import Execution
from zoe_client.scheduler_classes.container import Container


# Logs
def log_get(container_id: int) -> str:
    """
    Get the standard output/error of the processes running in the given container.

    :param container_id: the container to examine
    :return: a string containing the log
    """
    ipc_client = ZoeIPCClient()
    answer = ipc_client.ask('log_get', container_id=container_id)
    if answer is not None:
        return answer['log']


# Platform
def platform_stats() -> dict:
    """
    Platform-wide statistics that include Swarm and Zoe Scheduler data

    :return: the statistics. The format of this dictionary is not set in stone and could change.
    """
    ipc_client = ZoeIPCClient()
    stats = ipc_client.ask('platform_stats')
    return stats


# Containers
def container_stats(container_id: int) -> dict:
    """
    Get low-level statistics about a container. These come directly from Docker.

    :param container_id: The container to examine
    :return: the statistics. The format of this dictionary is not set in stone and could change.
    """
    ipc_client = ZoeIPCClient()
    return ipc_client.ask('container_stats', container_id=container_id)


def execution_exposed_url(execution: Execution) -> str:
    """
    Get the first main endpoint for a given application execution formatted as a URL.

    :param execution: the execution to use to build the URL
    :return: the endpoint URL
    """
    for c in execution.containers:
        assert isinstance(c, Container)
        port = c.description.exposed_endpoint()
        if port is not None:
            return port.get_url(c.ip_address)
