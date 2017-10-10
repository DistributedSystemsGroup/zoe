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

"""Parses Docker-specific configuration file."""

import configparser
import logging
from typing import List

from zoe_lib.config import get_conf

log = logging.getLogger(__name__)


class DockerHostConfig:
    """A class that holds static information about a host."""
    def __init__(self):
        self.name = None
        self.address = None
        self.external_address = None
        self.tls = False
        self.tls_cert = None
        self.tls_key = None
        self.tls_ca = None
        self.labels = []


class DockerConfig:
    """A class that holds the configuration for the Docker Engine backend."""
    def __init__(self):
        self.conffile = get_conf().backend_docker_config_file

    def read_config(self) -> List[DockerHostConfig]:
        """Parse the configuration file."""
        config = configparser.ConfigParser()
        config.read(self.conffile)
        hosts = []
        for section in config.sections():
            host = DockerHostConfig()
            host.name = section
            try:
                host.address = config[section]['docker_address']
                host.external_address = config[section]['external_address']
                host.tls = config.getboolean(section, 'use_tls')
                if host.tls:
                    host.tls_cert = config[section]['tls_cert']
                    host.tls_ca = config[section]['tls_ca']
                    host.tls_key = config[section]['tls_key']
            except KeyError as e:
                log.error('Error in Docker backend configuration, missing key {} in section {}'.format(e.args[0], section))
                continue

            if 'labels' in config[section]:  # labels are optional
                host.labels = config[section]['labels'].split(',')

            hosts.append(host)
        if len(hosts) == 0:
            log.error('Host list is empty, verify your docker backend configuration!')
        return hosts
