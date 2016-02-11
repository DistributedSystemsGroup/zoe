#!/usr/bin/python3

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

import logging
import time

from zoe_lib.swarm_client import SwarmClient
from zoe_observer.config import load_configuration, get_conf
from zoe_observer.swarm_event_manager import container_died
from zoe_observer.guest_inactivity import check_guests

log = logging.getLogger("main")


def main():
    """
    The entrypoint for the zoe-observer script.
    :return: int
    """
    load_configuration()
    args = get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger('kazoo').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.INFO)

    swarm = SwarmClient(args)

    while True:
        try:
            zoe_containers = swarm.list('zoe')
            for c in zoe_containers:
                if 'Exited' in c['status']:
                    zoe_id = c['labels']['zoe.container_id']
                    container_died(zoe_id)

            # check_guests(swarm)

        except KeyboardInterrupt:
            break
        except Exception:
            log.exception('Something bad happened')

        time.sleep(5)
