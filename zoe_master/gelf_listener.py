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

"""Zoe GELF listener."""

import socketserver
import gzip
import json
import logging
import threading
import os
import datetime

from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class GELFUDPHandler(socketserver.DatagramRequestHandler):
    """The handler for incoming UDP packets."""
    def handle(self):
        """Handle one UDP packet (one GELF log line in JSON format)."""
        data = self.rfile.read()
        data = gzip.decompress(data)
        data = json.loads(data.decode('utf-8'))
        deployment_name = data['_zoe_deployment_name']
        if deployment_name != get_conf().deployment_name:
            return

        execution_id = data['_zoe_execution_id']
        service_name = data['_zoe_service_name']
        host = data['host']
        timestamp = datetime.datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        message = data['short_message']

        log_file_path = os.path.join(get_conf().service_logs_base_path, get_conf().deployment_name, str(execution_id), service_name + '.txt')
        if not os.path.exists(log_file_path):
            os.makedirs(os.path.join(get_conf().service_logs_base_path, get_conf().deployment_name, str(execution_id)))
            open(log_file_path, 'w').write('ZOE HEADER: log file for service {} running on host {}\n'.format(service_name, host))

        with open(log_file_path, 'a') as logfile:
            logfile.write(timestamp + ' ' + message + '\n')


class ZoeLoggerUDPServer(socketserver.UDPServer):
    """The UDP server"""
    def __init__(self, server_address, handler_class):
        self.allow_reuse_address = True
        super().__init__(server_address, handler_class)


class GELFListener:
    """A thread that listens to UDP GELF and writes logs to a directory tree according to Zoe tags."""
    def __init__(self):
        self.server = ZoeLoggerUDPServer(("0.0.0.0", get_conf().gelf_listener), GELFUDPHandler)
        self.th = None
        self.start()

    def start(self):
        """Starts the GELF thread."""
        if self.th is not None:
            return
        log.info('GELF listener starting on {}:{}'.format("0.0.0.0", get_conf().gelf_listener))
        self.th = threading.Thread(target=self.server.serve_forever, name='GELF server', daemon=True)
        self.th.start()

    def quit(self):
        """Stops the GELF server."""
        self.server.shutdown()
        self.th.join(0.1)
