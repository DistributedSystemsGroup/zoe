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

from zoe_master.platform_manager import PlatformManager
from zoe_master.scheduler_policies import FIFOSchedulerPolicy
import zoe_master.config as config
from zoe_master.master_api import APIManager
from zoe_master.state.manager import StateManager
from zoe_master.state.blobs.fs import FSBlobs
from zoe_lib.metrics.influxdb import InfluxDBMetricSender
from zoe_lib.metrics.base import BaseMetricSender
from zoe_master.stats_manager import StatsManager
from zoe_master.workspace.filesystem import ZoeFSWorkspace

log = logging.getLogger("main")
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(name)s (%(threadName)s): %(message)s'


def main():
    """
    The entrypoint for the zoe-master script.
    :return: int
    """
    config.load_configuration()
    args = config.get_conf()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.INFO)
    logging.getLogger("tornado").setLevel(logging.DEBUG)
    logging.getLogger('passlib').setLevel(logging.INFO)

    log.info("Initializing state")
    state_manager = StateManager(FSBlobs)
    state_manager.init()
    config.singletons['state_manager'] = state_manager

    log.info("Initializing platform manager")
    pm = PlatformManager(FIFOSchedulerPolicy)
    config.singletons['platform_manager'] = pm

    log.info("Initializing workspace managers")
    fswk = ZoeFSWorkspace()
    config.singletons['workspace_managers'] = [fswk]

#    try:
    log.info("Checking state consistency")
    pm.check_workspaces()
    pm.check_state_swarm_consistency()
#    except:
#        log.error('State is seriously corrupted, delete and restart')

    if config.get_conf().influxdb_enable:
        metrics_th = InfluxDBMetricSender(config.get_conf())
        metrics_th.start()
        config.singletons['metric'] = metrics_th
    else:
        metrics_th = BaseMetricSender('metrics-logger', config.get_conf())
        config.singletons['metric'] = metrics_th

    stats_th = StatsManager()
#    stats_th.start()  # TODO Broken Docker API
    config.singletons['stats_manager'] = stats_th

    log.info("Starting ZMQ API server...")
    config.singletons['api_server'] = APIManager()
    config.singletons['api_server'].loop()
