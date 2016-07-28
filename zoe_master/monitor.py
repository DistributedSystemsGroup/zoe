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

"""Monitor for the Swarm event stream."""

import logging
import threading

from zoe_lib.swarm_client import SwarmClient
from zoe_lib.config import get_conf
from zoe_lib.sql_manager import SQLManager

log = logging.getLogger(__name__)


class ZoeMonitor(threading.Thread):
    """The monitor."""

    def __init__(self, state: SQLManager):
        super().__init__()
        self.setName('monitor')
        self.stop = False
        self.state = state
        self.setDaemon(True)

        self.start()

    def run(self):
        """The thread loop."""
        swarm = SwarmClient(get_conf())
        swarm.event_listener(lambda x: self._event_cb(x))

    def _event_cb(self, event: dict) -> bool:
        if event['Type'] == 'container':
            self._container_event(event)
        elif event['Type'] == 'network':
            pass
        elif event['Type'] == 'image':
            pass
        else:
            log.debug('Unmanaged event type: {}'.format(event['Type']))
            log.debug(event)

        if self.stop:
            return False
        else:
            return True

    def _container_event(self, event: dict):
        if 'zoe.deployment_name' not in event['Actor']['Attributes']:
            return
        if event['Actor']['Attributes']['zoe.deployment_name'] != get_conf().deployment_name:
            return

        service_id = event['Actor']['Attributes']['zoe.service.id']  # type: int
        service = self.state.service_list(only_one=True, id=service_id)
        if 'exec' in event['Action']:
            pass
        elif 'create' in event['Action']:
            service.set_docker_status('create')
        elif 'start' in event['Action']:
            service.set_docker_status('start')
        elif 'die' in event['Action']:
            service.set_docker_status('die')
        elif 'destroy' in event['Action']:
            service.set_docker_status('destroy')
        else:
            log.debug('Unmanaged container action: {}'.format(event['Action']))

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
