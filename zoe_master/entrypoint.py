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

import zoe_lib.config as config
from zoe_master.master_api import APIManager
from zoe_master.scheduler import ZoeScheduler
# from zoe_master.stats_manager import StatsManager
from zoe_master.workspace.filesystem import ZoeFSWorkspace
from zoe_master.execution_manager import restart_resubmit_scheduler

from zoe_lib.metrics.influxdb import InfluxDBMetricSender
from zoe_lib.metrics.base import BaseMetricSender
from zoe_lib.sql_manager import SQLManager

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

    logging.getLogger('kazoo').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.INFO)
    logging.getLogger("tornado").setLevel(logging.DEBUG)

    log.info("Initializing DB manager")
    config.singletons['sql_manager'] = SQLManager(args)

    log.info("Initializing workspace managers")
    fswk = ZoeFSWorkspace()
    config.singletons['workspace_managers'] = [fswk]

    if config.get_conf().influxdb_enable:
        metrics_th = InfluxDBMetricSender(config.get_conf())
        metrics_th.start()
        config.singletons['metric'] = metrics_th
    else:
        metrics_th = BaseMetricSender('metrics-logger', config.get_conf())
        config.singletons['metric'] = metrics_th

#    stats_th = StatsManager()
#    stats_th.start()  # TODO Broken Docker API
#    config.singletons['stats_manager'] = stats_th

    log.info("Initializing scheduler")
    config.scheduler = ZoeScheduler()

    restart_resubmit_scheduler()

    log.info("Starting ZMQ API server...")
    config.singletons['api_server'] = APIManager()

    try:
        config.singletons['api_server'].loop()
    except KeyboardInterrupt:
        pass
    except Exception:
        log.exception('fatal error')
    finally:
        config.scheduler.quit()
        config.singletons['api_server'].quit()
