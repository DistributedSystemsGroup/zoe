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

"""Zoe Master main entrypoint."""

import logging

from zoe_master.master_api import APIManager
from zoe_master.scheduler import ZoeScheduler
from zoe_master.size_scheduler import ZoeSizeBasedScheduler
from zoe_master.execution_manager import restart_resubmit_scheduler
from zoe_master.monitor import ZoeMonitor
from zoe_master.consistency import ZoeSwarmChecker

import zoe_lib.config as config
from zoe_lib.metrics.influxdb import InfluxDBMetricSender
from zoe_lib.metrics.logging import LogMetricSender
from zoe_lib.sql_manager import SQLManager

log = logging.getLogger("main")
LOG_FORMAT = '%(asctime)-15s %(levelname)s %(threadName)s->%(name)s: %(message)s'


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

    if config.get_conf().influxdb_enable:
        metrics = InfluxDBMetricSender(config.get_conf().deployment_name, config.get_conf().influxdb_url, config.get_conf().influxdb_dbname)
    else:
        metrics = LogMetricSender(config.get_conf().deployment_name)

    log.info("Initializing DB manager")
    state = SQLManager(args)

    log.info("Initializing scheduler")
    if False:
        scheduler = ZoeScheduler()
    else:
        scheduler = ZoeSizeBasedScheduler(state)

    monitor = ZoeMonitor(state)
    checker = ZoeSwarmChecker(state)

    restart_resubmit_scheduler(state, scheduler)

    log.info("Starting ZMQ API server...")
    api_server = APIManager(metrics, scheduler, state)

    try:
        api_server.loop()
    except KeyboardInterrupt:
        pass
    except Exception:
        log.exception('fatal error')
    finally:
        scheduler.quit()
        monitor.quit()
        checker.quit()
        api_server.quit()
        metrics.quit()
