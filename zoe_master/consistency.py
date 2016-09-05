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

"""Periodically try to integrate Swarm state into Zoe, since Swarm event stream fails randomly."""

import logging
import threading
import time

from zoe_lib.swarm_client import SwarmClient
from zoe_lib.config import get_conf
from zoe_lib.sql_manager import SQLManager, Service

log = logging.getLogger(__name__)

CHECK_INTERVAL = 300


class ZoeSwarmChecker(threading.Thread):
    """The Swarm Checker."""

    def __init__(self, state: SQLManager) -> None:
        super().__init__()
        self.setName('checker')
        self.stop = False
        self.state = state
        self.setDaemon(True)

        self.start()

    def run(self):
        """The thread loop."""
        log.info("Checker thread started")
        swarm = SwarmClient(get_conf())
        while not self.stop:
            service_list = self.state.service_list()
            container_list = swarm.list(only_label={'zoe.deployment_name': get_conf().deployment_name})

            for service in service_list:
                assert isinstance(service, Service)
                if service.status != service.DOCKER_START_STATUS:
                    pass
                found = False
                for container in container_list:
                    if container['id'] == service.docker_id:
                        found = True
                        if container['status'] == 'exited':
                            service.set_docker_status(service.DOCKER_DIE_STATUS)
                if not found:
                    service.set_docker_status(service.DOCKER_DESTROY_STATUS)

            time.sleep(CHECK_INTERVAL)

    def quit(self):
        """Stops the thread."""
        self.stop = True


SAMPLE_EVENT = {
    'node': {
        'Name': 'bf18',
        'Id': 'VPCL:E5GW:WON3:2DPV:WFO7:EVNO:ZAKS:V2PA:PGKU:RSM7:AAR3:EAV7',
        'Addr': '192.168.47.18:2375',
        'Ip': '192.168.47.18'
    },
    'timeNano': 1469622892143470822,
    'Actor': {
        'ID': 'e4d3e639c1ec2107262f19cf6e57406cf83e376ef4f131461c3f256d0ce64e13',
        'Attributes': {
            'node.ip': '192.168.47.18',
            'image': 'docker-registry:5000/zoerepo/spark-submit',
            'node.name': 'bf18',
            'node.addr': '192.168.47.18:2375',
            'zoe.service.name': 'spark-submit0',
            'name': 'spark-submit0-60-prod',
            'zoe.owner': 'milanesio',
            'zoe.deployment_name': 'prod',
            'com.docker.swarm.id': 'de7515d8839c461523e8326c552b45da0f9bd0f9af4f68d4d5a55429533405d4',
            'zoe.execution.id': '60',
            'zoe.monitor': 'true',
            'zoe.execution.name': 'testebob',
            'node.id': 'VPCL:E5GW:WON3:2DPV:WFO7:EVNO:ZAKS:V2PA:PGKU:RSM7:AAR3:EAV7',
            'zoe.service.id': '233',
            'zoe.type': 'app_service'
        }
    },
    'status': 'start',
    'Action': 'start',
    'id': 'e4d3e639c1ec2107262f19cf6e57406cf83e376ef4f131461c3f256d0ce64e13',
    'time': 1469622892,
    'Type': 'container',
    'from': 'docker-registry:5000/zoerepo/spark-submit node:bf18'
}
